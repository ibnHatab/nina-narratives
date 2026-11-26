import unittest

from monitors import Monitors


class MonitorTests(unittest.TestCase):
    first = dict(at=0, k=0, rule='ask', member='social', args=[], channel='hall')
    second = dict(first, at=5, k=1, rule='answer')

    def monitor(self, **spec):
        return Monitors([dict(id='test', member='social', scene='fixture', words='test', **spec)], {})

    def test_require_deadline(self):
        m = self.monitor(require=dict(rule='answer', by=4))
        m.check(self.second)
        self.assertEqual(len(m.finish(5, 1, {})), 1)
        m.check(dict(self.second, at=4))
        self.assertEqual(m.finish(5, 1, {}), [])

    def test_order(self):
        m = self.monitor(order=dict(first=dict(rule='ask'), second=dict(rule='answer')))
        self.assertEqual(len(m.check(self.second)), 1)
        m.check(self.first)
        self.assertEqual(m.check(self.second), [])

    def test_noninterference(self):
        m = self.monitor(never_reads=dict(member='social', channel='hall'))
        m.check(self.first)
        self.assertEqual(m.finish(0, 0, {'test': [self.first]}), [])
        self.assertEqual(len(m.finish(0, 0, {'test': [self.second]})), 1)
