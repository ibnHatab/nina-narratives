"""Recover a fresh Metis session from a synthetic durable decision journal."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from experiment import Observation, RETURN, Trial


def run():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed = 7
        original = Trial(seed, root / "first")
        original.observe(1, [RETURN])
        first_delivery = original.decide(1)
        journal = root / "journal.json"
        journal.write_text(json.dumps(dict(seed=seed, phases=original.phases)))
        expected = dict(original.shell.counts)
        original.recorder.close()
        del original

        data = json.loads(journal.read_text())
        recovered = Trial(data["seed"], root / "recovered")
        for row in data["phases"]:
            observations = [Observation(**o) for o in row["evidence"]]
            if row["phase"] == "observe":
                recovered.observe(row["epoch"], observations)
            else:
                # Restore the recorded input without sending any external command.
                recovered.phase(row["epoch"], row["phase"], row["inputs"], observations)
            replayed = recovered.phases[-1]
            assert replayed["after"] == row["after"]
            assert replayed["fired"] == row["fired"]
        assert recovered.shell.counts == expected
        assert recovered.task_in("spoken") == [first_delivery]
        recovered.observe(2, [RETURN])
        assert recovered.phases[-1]["inputs"] == []
        second_delivery = recovered.decide(2)
        assert first_delivery != second_delivery and second_delivery is not None
        recovered.recorder.close()
        print(f"Recovered {len(data['phases'])} phases. "
              f"Prior receipt: {first_delivery}. Next delivery: {second_delivery}.")


if __name__ == "__main__":
    run()
