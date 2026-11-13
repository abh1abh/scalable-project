QIS-NET Project 2 — Entanglement Distribution Network Simulator\*\*

Weight: Group work (~4 per group). Assigned Week 7, due end of Week 11 (see course page for exact dates). Week 9 milestone checkpoint is formative but strongly recommended.

**Your task.** Using the provided discrete-event simulation harness (`qnetsim.py`), build and **validate** a simulator for entanglement distribution on your group's assigned quantum network variant, then design a **policy** (purification and swapping decisions) that meets your variant's service-level objectives (rate, fidelity, p95 latency), and run a T2 sensitivity experiment with proper statistics. Full requirements are in the module's Project 2 specification.

**Your variant.** Your group's package (choose the variant corresponding to your group number e.g. group 3 is provided/chooses variant 3.) contains `variant_params.json` — your topology, physics parameters, workload, SLO targets and grading seeds — plus the four code files in the separate template folder. Variants differ per group: your SLOs and parameters are yours alone. In your variant_params.json it is important you first change the group from "unassigned" to your actual group number e.g. 3

**Submission (code, autograded).** One zip per group containing `simulator.py`, `policy.py`, `experiments.py` at the zip root. Unlimited resubmissions before the deadline; last one counts. Marking is automated against your variant: API conformance (10), validation against analytics (25), seeded determinism (10), SLO attainment (25), robustness across held-out seeds (10), experiment artefacts (20). Note: if validation scores below 15/25, SLO marks are capped — an unvalidated simulator earns little.

**Submission (report, video, code).** One PDF per group, max 8 pages: model description, validation evidence, policy design rationale, sensitivity results with confidence intervals, engineering conclusions against your SLOs, and a discussion of where classical networking concepts appear in your design (and where they break). Video max 3 mins. ALL group members appear in person. What you did, why, how, what you achieved overall, and the single achievement the group is proudest of.

**Rules.** Do not modify `qnetsim.py` (the autograder uses its own copy). numpy + standard library only. Group work within your group only; code similarity is screened across groups. Declare AI-assistant use in file headers. Each member completes the peer contribution form after submission.
