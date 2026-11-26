import unittest

from person_sim import Person
from scope import audience, grant_floor


class ChannelTest(unittest.TestCase):
    def test_overlapping_private_and_group_turns(self):
        private = dict(kind='floor', channel='direct')
        group = dict(kind='floor', channel='group')
        queue = []
        self.assertEqual(grant_floor([private, group], queue), [private])
        self.assertEqual(grant_floor([], queue), [group])
        people = {n: Person(n, {}) for n in ('one', 'two')}
        channels = {'direct': {'kind': 'private', 'people': ['one']},
                    'group': {'kind': 'group', 'people': list(people)}}
        self.assertEqual(audience(channels, 'direct', people, 0), [people['one']])
        self.assertEqual(audience(channels, 'group', people, 0), list(people.values()))
