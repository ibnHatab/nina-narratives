import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class ReplayTest(unittest.TestCase):
    def test_every_row_and_finding(self):
        root = Path(__file__).resolve().parents[1]
        cli = root / 'sitl/run.sh'
        fixture = root / 'workspaces/home/scenarios/cognition/b01-completed.yaml'
        with tempfile.TemporaryDirectory() as tmp:
            # This scenario intentionally violates its narrative expectation.
            run = subprocess.run([cli, fixture, '--out', tmp], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stderr)
            log = Path(tmp) / json.loads(run.stdout)['run'] / 'events.jsonl'
            good = subprocess.run([cli, '--replay', log], capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(good.stdout)['findings'][0]['monitor'], 'no-reminder-after-done')
            rows = log.read_text().splitlines()
            rows[-1] = json.dumps(dict(findings=[], world_hash='changed'))
            log.write_text('\n'.join(rows) + '\n')
            bad = subprocess.run([cli, '--replay', log], capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('diverged at row', bad.stderr)
