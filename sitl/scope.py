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
