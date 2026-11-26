// semworld-step folds Nina's world events through the semantic world one line at a time, for the SITL
// loop: the same Go world nina-live runs (pinned to nina-live's go.mod version), so a simulated day and a
// deployed day share one fold, one event alphabet and one surprise producer.
//
//	semworld-step -map home.map.json -member comfort=domains/comfort/domain.yaml < events.jsonl
//
// Input, one JSON object per line, in the order the loop decides (the world never reads a clock):
//
//	an event of the world stream: home.Event, {"at", "kind": ha_state|feed_down|command|report|conclude|
//	                              settle|strain|item|prefer|prior|curious, ...} (nina-live's log alphabet)
//	{"join": {"member": NAME, "manifest": PATH}}  a member starts reading the world's ports
//	{"hash": true}                                 ask for the checkpoint only
//
// Output, exactly one JSON object per input line, flushed: {"seq", "ok", "error"?, "out"?, "hash"}. "out" is
// home.Out: the surprises the event raised and, for a settle, each member's wake and level do-lines and the
// projected lines. A host takes members' lines from "out" and never asks the board itself (DESIGN.md §8). A
// settle's reply also carries "state", home.State(): the likeliest values the SITL projects to the families.
package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/metis-lang-dev/metis-worlds/libs/semantic-world/go/home"
	sw "github.com/metis-lang-dev/metis-worlds/libs/semantic-world/go/semworld"
)

type control struct {
	Join *struct {
		Member   string `json:"member"`
		Manifest string `json:"manifest"`
	} `json:"join"`
	Hash bool `json:"hash"`
}

type reply struct {
	Seq   int         `json:"seq"`
	OK    bool        `json:"ok"`
	Error string      `json:"error,omitempty"`
	Out   *home.Out   `json:"out,omitempty"`
	State *home.State `json:"state,omitempty"` // with a settle: the likeliest values, for the families (State())
	Hash  string      `json:"hash"`
}

func main() {
	mapPath := flag.String("map", "", "the home's map (home.map.json)")
	var joins []string
	flag.Func("member", "NAME=domain.yaml, a member reading the world's ports (repeatable)", func(s string) error {
		joins = append(joins, s)
		return nil
	})
	flag.Parse()
	if *mapPath == "" {
		fail(fmt.Errorf("-map is required"))
	}
	m, err := home.LoadMap(*mapPath)
	fail(err)
	h := home.New(m, home.DefaultParams)
	join := func(name, path string) error {
		man, err := sw.ReadManifest(path, name)
		if err != nil {
			return err
		}
		return h.B.Join(man)
	}
	for _, s := range joins {
		name, path, ok := cut(s)
		if !ok {
			fail(fmt.Errorf("-member %q: want NAME=PATH", s))
		}
		fail(join(name, path))
	}
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<24)
	out := bufio.NewWriter(os.Stdout)
	enc := json.NewEncoder(out)
	seq := 0
	for in.Scan() {
		line := in.Bytes()
		if len(line) == 0 {
			continue
		}
		seq++
		r := reply{Seq: seq, OK: true}
		var c control
		if err := json.Unmarshal(line, &c); err != nil {
			r.OK, r.Error = false, err.Error()
		} else if c.Join != nil {
			if err := join(c.Join.Member, c.Join.Manifest); err != nil {
				r.OK, r.Error = false, err.Error()
			}
		} else if !c.Hash {
			var ev home.Event
			if err := json.Unmarshal(line, &ev); err != nil {
				r.OK, r.Error = false, err.Error()
			} else if o, err := h.Apply(ev); err != nil {
				r.OK, r.Error = false, err.Error()
			} else {
				r.Out = &o
				if ev.Kind == "settle" {
					st := h.State()
					r.State = &st
				}
			}
		}
		r.Hash = h.Hash()
		fail(enc.Encode(r))
		fail(out.Flush())
	}
	fail(in.Err())
}

func cut(s string) (string, string, bool) {
	for i := range s {
		if s[i] == '=' {
			return s[:i], s[i+1:], true
		}
	}
	return "", "", false
}

func fail(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, "semworld-step:", err)
		os.Exit(1)
	}
}
