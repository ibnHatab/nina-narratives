"""Enforce the incarnation boundary before loading state or delivering an event."""


def check_paths(scope, workspace, world_map, record_root):
    if workspace.parent.name != scope or record_root != workspace.parent or not world_map.is_relative_to(record_root):
        raise ValueError(f'{scope} scenario references another workspace or world map')


def local_event(scope, event):
    return all(event.get(key, scope) == scope for key in ('origin', 'record_origin'))


def audience(channels, name, people, at):
    if not channels:
        return [p for p in people.values() if p.listens(name, at)]
    channel = channels[name]
    listeners = channel['people']
    if channel['kind'] not in ('public', 'group', 'private') or (channel['kind'] == 'private' and len(listeners) != 1):
        raise ValueError(f'invalid channel membership for {name}')
    return [people[n] for n in listeners if not people[n].away(at)]


def grant_floor(due, waiting):
    """The voice has one floor token. Queue simultaneous turns with their original channel."""
    waiting.extend(e for e in due if e.get('kind') == 'floor')
    if not waiting:
        return due
    grant = waiting.pop(0)
    # Keep the grant at the first opening in the outside event order.
    position = next((i for i, e in enumerate(due) if e.get('kind') == 'floor'), 0)
    events = [e for e in due if e.get('kind') != 'floor']
    events.insert(position, grant)
    return events
