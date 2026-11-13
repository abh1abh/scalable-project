import json

from policy import make_policy
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

held_out_seeds = params["grading"]["held_out_seeds"]

for held_out_seed in held_out_seeds:
    result = run_variant_scenario(params, sim_time, held_out_seed, policy)
    print(f"\nVariant scenario result for held-out seed {held_out_seed}:")
    for k, v in result.items():
        print(f"{k}: {v}")
