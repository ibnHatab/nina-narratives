# Why pack_propose refused the composition records (from the Metis agent, 2026-11-26)

Read from metis-agent `py/metis_agent` code by the Metis agent, not from our trace. Check it against the k=1 record.

- The divergence `{'k': 1, 'member': 'attention', 'what': 'why', 'want': 'none', 'got': None}` (trace.py `_compare`, l.547): in the live run `attention` did not beat at k=1 (`wake_why` "none", service.py `_beat_one` l.1688), but it took rows: a `take`/`step` item in its `seq`. Nothing delivered them in the replay.
- **Replayed:** a host's own tick do-lines, recorded as the member's `beat` item (`Tracer.beat_rows` l.175, replayed by `TraceHost.tick` l.391-435 when the record's why is not "none"). Also external lines served **outside** `Live.tick()` with kind take/world/intent/tool (`Tracer.traced_serve` l.86, `EXTERNAL` l.43, `_external` l.1399).
- **Not replayed:** `Live.take`/`Live.world` called **inside** a tick (from a host's tick, or a queue flushed during the tick) with any `by` other than `deliver` (`TraceHost.deliver` l.378, 488). `TraceHost.pending` is False (l.474).
- **Also required:** the image hash and protocol key match (trace.py 573, 593), and no host has `world_stepped` (l.571).
- **Fix:** each member's input comes from that member's own host tick (with `pending()`), or from the SITL loop calling `Live.take(d, lines, by=...)` **between** ticks. Never have one member's host push rows into another member's session during a tick. Run `replay_check` (mcp/tools/build.py l.129) on a short trace first: it prints the first divergence.
- **Per-member gating on a composition is supported:** `pack_propose` passes `--member` and `--composition` to the judge (build.py l.63-96); `replay_composition(candidate=...)` (trace.py l.561, 872, 1275). The precondition is a replaying baseline (`fired_diff` l.897). Specs: metis-lang spec 17 amendment 7, spec 15 §9.4, metis-loop docs/WORKSPACE.md §4.
