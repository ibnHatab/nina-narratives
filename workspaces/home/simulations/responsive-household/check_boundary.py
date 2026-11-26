"""Probe which guarantees the compiled rules supply before director routing.

Run with the Metis Python environment. Each query starts at the specified
boundary and uses the kernel's exact finite-horizon presence marginal.
"""
from dataclasses import replace
from pathlib import Path

from metis.kernel import ForwardProjection
from metis.lang.repl import Repl


PROGRAM = Path(__file__).with_name("household.llp")


def chance(program, initial, target, steps):
    state = dict.fromkeys(initial, 1)
    projection = ForwardProjection(replace(program, init=state), steps)
    return sum(mass for (_, counts), mass in projection.final.items()
               if dict(counts).get(target, 0))


def main():
    program = Repl(PROGRAM).prog
    queued = "state(call_one,queued)"
    committed = "state(call_one,committed)"
    spoken = "state(call_one,spoken)"
    reconcile = "reconcile(call_one)"
    # The second and third rows exercise the actual authorization boundary.
    probes = [
        ("queue without a grant", [queued], committed, 1, 0),
        ("queued and authorized", [queued, "authorize"], committed, 1, 1),
        ("completion and grant in one unordered batch",
         [queued, "authorize", reconcile], committed, 1, 0.5),
        ("commit without delivery acknowledgement", [committed], spoken, 1, 0),
        ("acknowledged delivery", [committed, "receipt(call_one)"], spoken, 1, 1),
        ("acknowledgement for a different instance",
         [committed, "receipt(call_two)"], spoken, 1, 0),
        ("wrong outing",
         ["promise(call_two,appointment)", "state(call_two,waiting)", "returned(errand)"],
         "state(call_two,ready)", 1, 0),
        ("same outing constant reused for a later promise",
         ["promise(call_two,appointment)", "state(call_two,waiting)", "returned(appointment)"],
         "state(call_two,ready)", 1, 1),
    ]
    for title, initial, target, steps, expected in probes:
        result = chance(program, initial, target, steps)
        print(f"{title}: {target} after {steps} step = {result:g}")
        if abs(result - expected) > 1e-9:
            raise AssertionError(f"{title}: expected {expected}, got {result}")


if __name__ == "__main__":
    main()
