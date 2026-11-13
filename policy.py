"""
policy.py — QIS-NET Project 2 policy (STUDENT FILE: replace the baseline).

The policy decides, each time a fresh pair arrives on a link, what to do:
swap immediately, purify first, hold, or discard aged pairs. Your variant's
SLOs (rate, fidelity, p95 latency) will typically NOT be met by the
baseline policy below.

Design space (see spec section 3.2):
  * purify while the freshest link fidelity is below a threshold AND a
    second pair is available on the same link;
  * hold vs swap rules (e.g., wait for a purified partner);
  * discard pairs whose current fidelity has fallen below a floor.

AI Usage:
No AI was used to write any of the code in this file.
"""

from qnetsim import bbpssw


class BaselinePolicy:
    """Swap-as-soon-as-possible; never purify. PROVIDED as the baseline.
    It meets the reference scenarios' expectations but is deliberately
    insufficient for most variant SLOs."""

    def __init__(self, params):
        self.params = params
        # map each repeater node to its adjacent link pairs for swapping
        self.chains = params["policy"]["swap_chains"]  # list of [left, right]

    def on_pair_ready(self, link, pair, state, sim):
        for left, right in self.chains:
            if state.pairs.get(left) and state.pairs.get(right):
                sim.swap(left, right)


class FreshAndDiscardSwapPolicy:
    def __init__(self, params):
        self.params = params
        self.chains = params["policy"]["swap_chains"]
        self.min_fidelity = params["slo"]["min_fidelity"] / (
            params["physics"]["f_swap"] * params["physics"]["f_link"]
        )
        rates = [
            link["attempt_rate"] * link["p_success"]
            for link in params["topology"]["links"]
        ]
        self.slow_links_index = rates.index(min(rates))

    def on_pair_ready(self, link, pair, state, sim):
        for link_id, inv in state.pairs.items():
            if link_id == self.slow_links_index:
                continue
            while inv and state.current_fidelity(inv[0]) < self.min_fidelity:
                sim.discard(link_id, 0)

        for left, right in self.chains:
            if state.pairs.get(left) and state.pairs.get(right):
                sim.swap(left, right, left_index=-1, right_index=-1)


class PurifyPolicy:
    def __init__(self, params):
        self.params = params
        self.chains = params["policy"]["swap_chains"]
        self.min_fidelity = params["slo"]["min_fidelity"] / (
            params["physics"]["f_swap"] * params["physics"]["f_link"]
        )
        rates = [
            link["attempt_rate"] * link["p_success"]
            for link in params["topology"]["links"]
        ]
        self.slow_links_index = rates.index(min(rates))

    def on_pair_ready(self, link, pair, state, sim):
        for link_id, inv in state.pairs.items():
            if link_id == self.slow_links_index or len(inv) < 2:
                continue

            f0 = state.current_fidelity(inv[0])
            f1 = state.current_fidelity(inv[1])
            f_out, _ = bbpssw(min(f0, f1))

            if f_out > max(f0, f1):
                f_out, _ = bbpssw(min(f0, f1))
                sim.purify(link_id)

        for left, right in self.chains:
            l, r = state.pairs.get(left), state.pairs.get(right)
            if l and r:
                li = max(range(len(l)), key=lambda i: state.current_fidelity(l[i]))
                ri = max(range(len(r)), key=lambda i: state.current_fidelity(r[i]))
                sim.swap(left, right, left_index=li, right_index=ri)


def make_policy(params):
    """Return your policy object. Replace BaselinePolicy with your own class
    (same constructor signature and on_pair_ready hook)."""
    return FreshAndDiscardSwapPolicy(params)
