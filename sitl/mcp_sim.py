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
