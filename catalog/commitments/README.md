# Commitments
Sources: B01-C01, C06, C08.
Candidate state: commitment(owner, beneficiary, goal, status), trigger, deadline, dependency, reminder, decision provenance.
Transitions: create, renegotiate trigger, become due, acknowledge, fulfill, cancel, reconcile after outage.
Interfaces: calendar, tasks, timers, situations, attention.
Invariants: notification is not fulfillment; a new circumstance does not automatically reverse an authorized decision; condition-based reminders are not arbitrary clock timers. Check duplicate firing and overdue reconciliation.

Status: narrative-derived design brief; not executable or validated Metis syntax.
