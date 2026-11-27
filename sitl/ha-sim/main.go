// ha-sim is Home Assistant as Nina sees it, for the SITL with Nina in the loop (sitl/NINA-IN-THE-LOOP.md):
// the REST and websocket surface acasa's hass client uses, and nothing else. It is a transport: the house's
// truth is the loop's (sitl/nina_proc.py, mcp_sim.HomeAssistantSim). Every service call Nina makes is
// reported on stdout as the command it is; it changes nothing here until the loop says what the house did.
//
//	ha-sim -token TOKEN [-addr 127.0.0.1:0]
//
// stdout, one JSON object a line: {"ready": "http://127.0.0.1:PORT"} first, then
// {"call": {"domain", "service", "data", "response"}} as Nina calls, {"write": {"entity_id", "state", ...}}
// when she writes a state (POST /api/states/<id>), {"reply": n} for each control line.
//
// stdin (the loop), one JSON object a line:
//
//	{"set": {"entity_id", "state", "attributes"}}   the house's state now (a state_changed to her)
//	{"states": [...]}                                 several at once (the scenario's start)
//	{"config": {...}}                                 /api/config (location_name, latitude, …, time_zone)
//	{"responses": {"todo.get_items": {...}}}          what a service with return_response answers
package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

type state struct {
	EntityID    string         `json:"entity_id"`
	State       string         `json:"state"`
	Attributes  map[string]any `json:"attributes"`
	LastChanged string         `json:"last_changed"`
	LastUpdated string         `json:"last_updated"`
}

type server struct {
	token string

	mu        sync.Mutex
	states    map[string]*state
	config    map[string]any
	responses map[string]any
	subs      map[*websocket.Conn]*sync.Mutex

	out sync.Mutex
}

func (s *server) emit(v any) {
	b, _ := json.Marshal(v)
	s.out.Lock()
	os.Stdout.Write(append(b, '\n'))
	s.out.Unlock()
}

func now() string { return time.Now().UTC().Format(time.RFC3339Nano) }

func (s *server) set(st state) {
	if st.Attributes == nil {
		st.Attributes = map[string]any{}
	}
	t := now()
	s.mu.Lock()
	if old, ok := s.states[st.EntityID]; ok && old.State == st.State {
		st.LastChanged = old.LastChanged
	} else {
		st.LastChanged = t
	}
	st.LastUpdated = t
	cp := st
	s.states[st.EntityID] = &cp
	subs := make(map[*websocket.Conn]*sync.Mutex, len(s.subs))
	for c, m := range s.subs {
		subs[c] = m
	}
	s.mu.Unlock()
	ev := map[string]any{"id": 2, "type": "event", "event": map[string]any{"event_type": "state_changed",
		"data": map[string]any{"entity_id": cp.EntityID, "new_state": cp}, "time_fired": t}}
	for c, m := range subs {
		m.Lock()
		_ = c.WriteJSON(ev)
		m.Unlock()
	}
}

func (s *server) authed(w http.ResponseWriter, r *http.Request) bool {
	if r.Header.Get("Authorization") != "Bearer "+s.token {
		http.Error(w, `{"message":"401: Unauthorized"}`, http.StatusUnauthorized)
		return false
	}
	return true
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}

func (s *server) api(w http.ResponseWriter, r *http.Request) {
	if !s.authed(w, r) {
		return
	}
	p := strings.TrimPrefix(r.URL.Path, "/api")
	switch {
	case p == "/" || p == "":
		writeJSON(w, map[string]string{"message": "API running."})
	case p == "/config":
		s.mu.Lock()
		c := s.config
		s.mu.Unlock()
		writeJSON(w, c)
	case p == "/states" && r.Method == "GET":
		s.mu.Lock()
		all := []*state{}
		for _, st := range s.states {
			all = append(all, st)
		}
		s.mu.Unlock()
		writeJSON(w, all)
	case strings.HasPrefix(p, "/states/"):
		id := strings.TrimPrefix(p, "/states/")
		if r.Method == "POST" { // her own sensors (sensor.nina_persona): a state she writes
			var st state
			json.NewDecoder(r.Body).Decode(&st)
			st.EntityID = id
			s.emit(map[string]any{"write": st})
			s.set(st)
			writeJSON(w, st)
			return
		}
		s.mu.Lock()
		st, ok := s.states[id]
		s.mu.Unlock()
		if !ok {
			http.Error(w, `{"message":"Entity not found."}`, http.StatusNotFound)
			return
		}
		writeJSON(w, st)
	case strings.HasPrefix(p, "/services/"):
		parts := strings.SplitN(strings.TrimPrefix(p, "/services/"), "/", 2)
		if len(parts) != 2 {
			http.Error(w, "bad service", 400)
			return
		}
		var data map[string]any
		json.NewDecoder(r.Body).Decode(&data)
		_, response := r.URL.Query()["return_response"]
		s.emit(map[string]any{"call": map[string]any{"domain": parts[0], "service": parts[1], "data": data, "response": response}})
		if response {
			s.mu.Lock()
			resp := s.responses[parts[0]+"."+parts[1]]
			s.mu.Unlock()
			if resp == nil {
				resp = map[string]any{}
			}
			writeJSON(w, map[string]any{"changed_states": []any{}, "service_response": resp})
			return
		}
		writeJSON(w, []any{}) // the states it changed: none yet; the loop says what the house did
	default:
		http.Error(w, `{"message":"Not found."}`, http.StatusNotFound)
	}
}

var upgrader = websocket.Upgrader{CheckOrigin: func(*http.Request) bool { return true }}

func (s *server) ws(w http.ResponseWriter, r *http.Request) {
	c, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	defer c.Close()
	m := &sync.Mutex{}
	write := func(v any) { m.Lock(); _ = c.WriteJSON(v); m.Unlock() }
	write(map[string]any{"type": "auth_required", "ha_version": "sitl"})
	var auth struct {
		Type        string `json:"type"`
		AccessToken string `json:"access_token"`
	}
	if c.ReadJSON(&auth) != nil || auth.AccessToken != s.token {
		write(map[string]any{"type": "auth_invalid", "message": "Invalid access token"})
		return
	}
	write(map[string]any{"type": "auth_ok", "ha_version": "sitl"})
	for {
		var msg map[string]any
		if c.ReadJSON(&msg) != nil {
			s.mu.Lock()
			delete(s.subs, c)
			s.mu.Unlock()
			return
		}
		id := msg["id"]
		switch msg["type"] {
		case "get_states":
			s.mu.Lock()
			all := []*state{}
			for _, st := range s.states {
				all = append(all, st)
			}
			s.mu.Unlock()
			write(map[string]any{"id": id, "type": "result", "success": true, "result": all})
		case "subscribe_events":
			s.mu.Lock()
			s.subs[c] = m
			s.mu.Unlock()
			write(map[string]any{"id": id, "type": "result", "success": true, "result": nil})
		default:
			write(map[string]any{"id": id, "type": "result", "success": true, "result": nil})
		}
	}
}

func main() {
	token := flag.String("token", "sitl", "the token Nina's config names (its file's contents)")
	addr := flag.String("addr", "127.0.0.1:0", "where to listen")
	flag.Parse()
	s := &server{token: *token, states: map[string]*state{}, subs: map[*websocket.Conn]*sync.Mutex{},
		config:    map[string]any{"location_name": "Home", "latitude": 45.75, "longitude": 21.23, "time_zone": "Europe/Bucharest", "version": "sitl"},
		responses: map[string]any{}}
	ln, err := net.Listen("tcp", *addr)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/api/websocket", s.ws)
	mux.HandleFunc("/mcp", s.mcp) // ha-mcp's two tools Nina uses with hass.via mcp (acasa hass.MCP)
	mux.HandleFunc("/api/", s.api)
	go http.Serve(ln, mux)
	s.emit(map[string]any{"ready": "http://" + ln.Addr().String()})
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<24)
	n := 0
	for in.Scan() {
		var ctl struct {
			Set       *state         `json:"set"`
			States    []state        `json:"states"`
			Config    map[string]any `json:"config"`
			Responses map[string]any `json:"responses"`
		}
		n++
		if json.Unmarshal(in.Bytes(), &ctl) != nil {
			s.emit(map[string]any{"reply": n, "error": "not JSON"})
			continue
		}
		if ctl.Set != nil {
			s.set(*ctl.Set)
		}
		for _, st := range ctl.States {
			s.set(st)
		}
		s.mu.Lock()
		for k, v := range ctl.Config {
			s.config[k] = v
		}
		for k, v := range ctl.Responses {
			s.responses[k] = v
		}
		s.mu.Unlock()
		s.emit(map[string]any{"reply": n})
	}
}

// mcp is ha-mcp as acasa's hass.MCP calls it (Streamable HTTP, JSON answers): ha_call_service, reported on
// stdout as a REST call is (the loop's house answers it), and ha_get_state from the states held here.
func (s *server) mcp(w http.ResponseWriter, r *http.Request) {
	var msg struct {
		ID     any            `json:"id"`
		Method string         `json:"method"`
		Params map[string]any `json:"params"`
	}
	if json.NewDecoder(r.Body).Decode(&msg) != nil {
		http.Error(w, "not JSON-RPC", 400)
		return
	}
	if msg.ID == nil { // a notification
		w.WriteHeader(http.StatusAccepted)
		return
	}
	w.Header().Set("Mcp-Session-Id", "sitl")
	text := func(v any, isErr bool) map[string]any {
		b, _ := json.Marshal(v)
		return map[string]any{"content": []any{map[string]any{"type": "text", "text": string(b)}}, "isError": isErr}
	}
	var result any
	switch msg.Method {
	case "initialize":
		result = map[string]any{"protocolVersion": "2025-03-26", "capabilities": map[string]any{"tools": map[string]any{}},
			"serverInfo": map[string]any{"name": "ha-sim", "version": "1"}}
	case "tools/list":
		result = map[string]any{"tools": []any{
			map[string]any{"name": "ha_call_service", "description": "a service call", "inputSchema": map[string]any{"type": "object"}},
			map[string]any{"name": "ha_get_state", "description": "entities' states", "inputSchema": map[string]any{"type": "object"}}}}
	case "tools/call":
		name, _ := msg.Params["name"].(string)
		args, _ := msg.Params["arguments"].(map[string]any)
		switch name {
		case "ha_call_service":
			data, _ := args["data"].(map[string]any)
			if data == nil {
				data = map[string]any{}
			}
			if e, ok := args["entity_id"]; ok {
				data["entity_id"] = e
			}
			s.emit(map[string]any{"call": map[string]any{"domain": args["domain"], "service": args["service"], "data": data, "response": false, "via": "mcp"}})
			result = text(map[string]any{"success": true}, false)
		case "ha_get_state":
			var ids []string
			switch e := args["entity_id"].(type) {
			case string:
				ids = []string{e}
			case []any:
				for _, x := range e {
					if id, ok := x.(string); ok {
						ids = append(ids, id)
					}
				}
			}
			s.mu.Lock()
			sts := map[string]any{}
			for _, id := range ids {
				if st, ok := s.states[id]; ok {
					sts[id] = map[string]any{"entity_id": st.EntityID, "state": st.State, "attributes": st.Attributes}
				}
			}
			s.mu.Unlock()
			result = text(map[string]any{"success": len(sts) > 0, "count": len(sts), "states": sts}, false)
		default:
			result = text(map[string]any{"success": false, "error": "no tool " + name}, true)
		}
	default:
		writeJSON(w, map[string]any{"jsonrpc": "2.0", "id": msg.ID, "error": map[string]any{"code": -32601, "message": "no method " + msg.Method}})
		return
	}
	writeJSON(w, map[string]any{"jsonrpc": "2.0", "id": msg.ID, "result": result})
}
