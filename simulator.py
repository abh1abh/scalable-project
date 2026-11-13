"""
simulator.py — QIS-NET Project 2 runner (STUDENT FILE: complete the TODOs).

Drive the provided harness (qnetsim.py) to implement the three graded
entry points. Signatures are normative; the autograder imports them.

Only numpy + standard library + qnetsim may be used.

AI Usage:
AI was used verify that we understood the qnetsim functionality properly and the variant_params.json file.
AI was also used to help us understand how to implement the p95_latency_ms metric.
Specifically how to calculate the latency of each delivered pair and how to calculate the p95 latency from that list of latencies.
AI was not used to write any of the code in this file. All code was written by the team.
"""

import math

import numpy as np

from qnetsim import DeliveredPair, Link, Simulator, summarise

# ---------------------------------------------------------------- helpers


def make_links(params, which="variant"):
    """Build Link objects from the variant parameter dict.

    `which="one_hop"` / `"two_hop"` select the reference scenarios defined in
    params["reference"]; `which="variant"` builds the full variant topology.
    PROVIDED — you should not need to change this.
    """
    links = []
    if which == "one_hop":
        ref = params["reference"]["one_hop"]
        links.append(
            Link(
                link_id=0,
                nodes=(0, 1),
                attempt_rate=ref["attempt_rate"],
                p_success=ref["p_success"],
                f_link=params["physics"]["f_link"],
            )
        )
    elif which == "two_hop":
        ref = params["reference"]["two_hop"]
        for i, lp in enumerate(ref["links"]):
            links.append(
                Link(
                    link_id=i,
                    nodes=(i, i + 1),
                    attempt_rate=lp["attempt_rate"],
                    p_success=lp["p_success"],
                    f_link=params["physics"]["f_link"],
                )
            )
    else:
        for i, lp in enumerate(params["topology"]["links"]):
            links.append(
                Link(
                    link_id=i,
                    nodes=tuple(lp["nodes"]),
                    attempt_rate=lp["attempt_rate"],
                    p_success=lp["p_success"],
                    f_link=params["physics"]["f_link"],
                )
            )
    return links


def request_times(params, sim_time_ms, seed):
    """Deterministic request arrival times (ms) for the variant workload.
    Uses a generator derived from `seed` so runs are reproducible.
    PROVIDED."""
    wl = params["workload"]
    rng = np.random.default_rng(seed + 7919)
    t, times = 0.0, []
    while True:
        t += rng.exponential(1000.0 / wl["arrival_rate_per_s"])
        if t > sim_time_ms:
            break
        times.append(t)
    return times


# ---------------------------------------------------------------- graded entry points


def run_one_hop(params, sim_time_ms, seed) -> dict:
    """Reference scenario: a single elementary link, no swapping.
    Return {"rate": ..., "mean_fidelity": ...}.

    TODO: build the one-hop links, run the Simulator for sim_time_ms with
    policy=None, and use qnetsim.summarise on a delivered-list you fill
    yourself (every generated pair counts as delivered here — record
    deliveries via a tiny inline policy or by reading state.pairs/stats).

    HINT: the harness only records `delivered` on swap; for the one-hop
    case, write a 3-line policy class whose on_pair_ready appends a
    DeliveredPair-equivalent record (or count pairs via state.stats and
    track fidelities in a list).
    """
    links = make_links(params, which="one_hop")
    sim = Simulator(
        links,
        t2=math.inf,
        q_swap=1.0,
        f_swap=1.0,
        seed=seed,
        purification_allowed=False,
    )
    sim.run(sim_time_ms, policy=None)
    delivered = []
    for pair in sim.state.pairs.get(0, []):
        delivered.append(
            DeliveredPair(
                request_id=-1,
                delivered_at=pair.born,
                fidelity=pair.f0,
                consumed=1,
            )
        )

    summary = summarise(delivered, sim_time_ms)
    return {"rate": summary["rate"], "mean_fidelity": summary["mean_fidelity"]}


class ASAPSwapPolicy:
    def on_pair_ready(self, link, pair, state, sim):
        if state.pairs.get(0) and state.pairs.get(1):
            sim.swap(0, 1)


def run_two_hop(params, sim_time_ms, seed) -> dict:
    """Reference scenario: two links, one repeater, immediate swap,
    T2 = infinity, q_swap = 1 (params['reference']['two_hop']).
    Return {"rate": ..., "mean_fidelity": ...}.

    TODO: build links, construct the Simulator with t2=math.inf,
    q_swap=1.0, f_swap=params['physics']['f_swap']; use a policy that swaps
    as soon as both links hold a pair; summarise with qnetsim.summarise.
    """

    links = make_links(params, which="two_hop")
    sim = Simulator(
        links,
        t2=math.inf,
        q_swap=1.0,
        f_swap=params["physics"]["f_swap"],
        seed=seed,
        purification_allowed=False,
    )

    delivered = sim.run(sim_time_ms, policy=ASAPSwapPolicy())
    summary = summarise(delivered, sim_time_ms)
    return {"rate": summary["rate"], "mean_fidelity": summary["mean_fidelity"]}


def run_variant_scenario(params, sim_time_ms, seed, policy) -> dict:
    """Full variant scenario with YOUR policy.
    Return {"rate": ..., "mean_fidelity": ..., "p95_latency_ms": ...,
            "pairs_consumed_per_delivery": ...}.

    TODO:
      * build the variant topology links;
      * construct the Simulator with your variant's physics
        (t2, q_swap, f_swap, purification_allowed, seed);
      * generate request_times(...); use a pooled unlimited end-to-end buffer.
        A request consumes a buffered pair at zero latency, or queues FIFO
        for a later delivery. Exclude unserved requests from p95. Fidelity
        is measured at generation; this buffer does not model further decay;
      * return the four metrics. pairs_consumed_per_delivery =
        stats['generated'] / max(1, delivered).
    """
    links = make_links(params)
    sim = Simulator(
        links,
        t2=params["physics"]["t2_ms"],
        q_swap=params["physics"]["q_swap"],
        f_swap=params["physics"]["f_swap"],
        seed=seed,
        purification_allowed=params["physics"]["purification_allowed"],
    )

    delivered = sim.run(sim_time_ms, policy=policy)

    deliver_times = [d.delivered_at for d in delivered]
    req_times = request_times(params, sim_time_ms, seed)

    latency = []
    for i in range(min(len(deliver_times), len(req_times))):
        latency.append(max(0, deliver_times[i] - max(0, req_times[i])))

    lats = sorted(latency)
    p95 = (
        lats[min(len(lats) - 1, int(math.ceil(0.95 * len(lats))) - 1)] if lats else 0.0
    )

    summary = summarise(delivered, sim_time_ms)
    return {
        "rate": summary["rate"],
        "mean_fidelity": summary["mean_fidelity"],
        "p95_latency_ms": p95,
        "pairs_consumed_per_delivery": sim.state.stats["generated"]
        / max(1, summary["delivered"]),
    }
