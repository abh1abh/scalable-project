import json

from experiments import mean_ci95
from policy import BaselinePolicy, make_policy
from simulator import run_one_hop, run_two_hop, run_variant_scenario

params = json.load(open("variant_params.json"))
seed = params["grading"]["seed"]
sim_time = params["grading"]["sim_time_ms"]

result = run_one_hop(params, sim_time, seed)
print("One-hop scenario result:")
print(result)
print("expected rate:", params["reference"]["expected"]["one_hop_rate"])

print("\n")

result = run_two_hop(params, sim_time, seed)
print("Two-hop scenario result:")
print(result)
print("expected rate:", params["reference"]["expected"]["two_hop_rate"])

print("\n")

policy = make_policy(params)
result = run_variant_scenario(params, sim_time, seed, policy)
print(f"Variant scenario result for seed {seed}:")
for k, v in result.items():
    print(f"{k}: {v}")

# For policy comparison
experiment_seeds = params["experiment"]["seeds"]

experiment_seeds = params["experiment"]["seeds"]
metrics = ["rate", "mean_fidelity", "pairs_consumed_per_delivery"]

for name, make in [("Baseline", BaselinePolicy), ("Implemented", make_policy)]:
    results = [
        run_variant_scenario(params, sim_time, s, make(params))
        for s in experiment_seeds
    ]
    print(f"\n Policy {name}:")
    for k in metrics:
        mean, ci = mean_ci95([r[k] for r in results])
        print(f"{k}: {mean:.4f} ± {ci:.4f}")

# For SLO comparison

seeds = [seed] + params["grading"]["held_out_seeds"]
for seed in seeds:
    r = run_variant_scenario(params, sim_time, seed, make_policy(params))
    print(
        f"\nSeed {seed}: Rate = {r['rate']}, Fidelity = {r['mean_fidelity']}, Latency = {r['p95_latency_ms']}"
    )


# Determinism check
def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    assert ok, name


def check_determinism():
    for seed in [params["grading"]["seed"]] + params["grading"]["held_out_seeds"]:
        a = run_variant_scenario(params, sim_time, seed, make_policy(params))
        b = run_variant_scenario(params, sim_time, seed, make_policy(params))
        check(f"same seed gives identical results, seed {seed}", a == b, str(a))

    a = run_variant_scenario(
        params, sim_time, params["grading"]["seed"], make_policy(params)
    )
    b = run_variant_scenario(
        params, sim_time, params["grading"]["held_out_seeds"][0], make_policy(params)
    )
    check("different seeds give different results", a != b)


check_determinism()

experiment_seeds = params["experiment"]["seeds"]
# T_2 sensitivity check
for t2 in params["experiment"]["t2_grid_ms"]:
    p = json.loads(json.dumps(params))
    p["physics"]["t2_ms"] = t2
    results = [
        run_variant_scenario(p, sim_time, s, make_policy(p)) for s in experiment_seeds
    ]

    rate_mean, rate_ci = mean_ci95([r["rate"] for r in results])
    f_mean, f_ci = mean_ci95([r["mean_fidelity"] for r in results])
    print(t2, f"rate {rate_mean:.2f} ± {rate_ci:.2f}", f"F {f_mean:.4f} ± {f_ci:.4f}")
