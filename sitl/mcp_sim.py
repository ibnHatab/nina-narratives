"""A simulated MCP server for the SITL. Its tools are Home Assistant's, with the hidden truth behind them.

The loop calls `call(tool, args, at, cid)` exactly where nina-live calls Home Assistant's MCP server. The
result is the tool's answer, and its *effect* is the readings it schedules: ha_state events the loop folds into the
semantic world when their time comes. A device that ignores the call schedules nothing. The world, not this
module, then notices: no reading within the command's grace is the world's own surprise.

Truth per device role (the scenario's `truth.devices`): {obeys: true|false, delay_s: s}. Only this module and the
scenario's monitors read it. No member does.
"""


class HomeAssistantSim:
    TOOLS = ('HassTurnOn', 'HassTurnOff', 'HassFanSetPresetMode')

    def __init__(self, truth=None):
        self.truth = truth or {}
        self.calls = []            # (at, cid, tool, args, answer): the server's own log

    def _device(self, role):
        return {'obeys': True, 'delay_s': 2, **(self.truth.get(role) or {})}

    def call(self, tool, args, at, cid, role):
        """(answer, [(at, ha_state)]) for one tools/call."""
        if tool not in self.TOOLS:
            answer = {'isError': True, 'text': 'unknown tool %s' % tool}
            self.calls.append((at, cid, tool, args, answer))
            return answer, []
        dev = self._device(role)
        names = args['name'] if isinstance(args['name'], list) else [args['name']]
        answer = {'isError': False, 'text': '%s %s' % (tool, ' '.join(names))}
        self.calls.append((at, cid, tool, args, answer))
        if not dev['obeys']:
            return answer, []          # HA accepted the call; the device did not move
        when = at + float(dev['delay_s'])
        if tool == 'HassFanSetPresetMode':
            state = {'entity_id': names[0], 'state': 'on', 'attributes': {'preset_mode': args['preset_mode']}}
            return answer, [(when, state)]
        state = 'on' if tool == 'HassTurnOn' else 'off'
        return answer, [(when, {'entity_id': n, 'state': state, 'attributes': {}}) for n in names]


def discovery(m, at):
    """The initial get_states: every entity the map names, as discovered. Devices off, rooms empty."""
    out = []
    for d in (m.get('lights') or {}).values():
        if d.get('entity'):
            out.append({'entity_id': d['entity'], 'state': 'off', 'attributes': {}})
    for d in (m.get('units') or {}).values():
        for f in ('supply', 'extract'):
            out.append({'entity_id': 'fan.%s_%s_fan' % (d['prefix'], f), 'state': 'off', 'attributes': {}})
        for sv in ('heater', 'winter'):
            out.append({'entity_id': 'switch.%s_%s' % (d['prefix'], sv), 'state': 'off', 'attributes': {}})
    for d in (m.get('tvs') or {}).values():
        if d.get('entity'):
            out.append({'entity_id': d['entity'], 'state': 'off', 'attributes': {}})
    for r, e in (m.get('radar') or {}).items():
        if e and not r.startswith('_'):
            out.append({'entity_id': e, 'state': 'off', 'attributes': {}})
    out.append({'entity_id': m.get('sun', 'sun.sun'), 'state': 'above_horizon', 'attributes': {}})
    return [{'at': at, 'kind': 'ha_state', 'ha': s} for s in out]


def device_command(rule, contract, command, role, world_map):
    """Resolve a contract's role and per-rule binding into a prediction and an MCP call."""
    import re

    context = dict(world_map[contract['role_map']][role])
    context.update(contract.get('values', {}).get(rule, {}))

    def render(value):
        if isinstance(value, dict):
            return {k: render(v) for k, v in value.items()}
        if isinstance(value, list):
            return [render(v) for v in value]
        if not isinstance(value, str):
            return value
        token = re.fullmatch(r'\{([^{}]+)\}', value)
        if token:
            return context[token[1]]
        return re.sub(r'\{([^{}]+)\}', lambda m: str(context[m[1]]), value)

    for key, template in contract.get('bindings', {}).items():
        if '{' + key + '}' in str(command):
            context[key] = render(template)
    mcp = render(command['adapter']['mcp'])
    return render(command['predicts']), mcp['tool'], mcp['args']
