import json
import math

import numpy as np
from scipy import stats

from simulator import run_one_hop, run_two_hop

# Added to the seeds from variant_params.json to reach n = 20 for the confidence interval.
EXTRA_SEEDS = list(range(100, 111))

# Seeds used for the convergence check (the first 10 of the 20).
CONVERGENCE_N_SEEDS = 10
CONVERGENCE_TIMES_S = [10, 30, 100, 300]


def build_seeds(params):
    g = params["grading"]
    return [g["seed"]] + g["held_out_seeds"] + params["experiment"]["seeds"] + EXTRA_SEEDS


def mean_ci95(values):
    """Mean and 95% t-interval half-width (df = n - 1)."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    sd = values.std(ddof=1)
    t = stats.t.ppf(0.975, df=n - 1)
    return float(values.mean()), float(t * sd / math.sqrt(n)), float(sd)


def check_scenario(name, run, params, seeds, sim_time_ms, expected_rate, expected_fid):
    tol = params["grading"]["tolerances"]
    results = [run(params, sim_time_ms, s) for s in seeds]
    rates = np.array([r["rate"] for r in results])
    fids = np.array([r["mean_fidelity"] for r in results])

    rate_mean, rate_ci, rate_sd = mean_ci95(rates)
    fid_mean, fid_ci, _ = mean_ci95(fids)
    rate_err = (rates - expected_rate) / expected_rate
    worst = int(np.argmax(np.abs(rate_err)))
    t_seconds = sim_time_ms / 1000.0

    return {
        "scenario": name,
        "rate": {
            "analytic": expected_rate,
            "grading_seed": float(rates[0]),
            "grading_seed_err_pct": 100 * float(rate_err[0]),
            "mean": rate_mean,
            "ci95": rate_ci,
            "mean_err_pct": 100 * (rate_mean - expected_rate) / expected_rate,
            "within_tol": int(np.sum(np.abs(rate_err) <= tol["rate_rel"])),
        },
        "fidelity": {
            "analytic": expected_fid,
            "grading_seed": float(fids[0]),
            "grading_seed_err": float(fids[0] - expected_fid),
            "mean": fid_mean,
            "ci95": fid_ci,
            "mean_err": fid_mean - expected_fid,
            "within_tol": int(np.sum(np.abs(fids - expected_fid) <= tol["fid_abs"])),
        },
        "worst_seed": {"seed": seeds[worst], "rate": float(rates[worst]),
                       "err_pct": 100 * float(rate_err[worst])},
        "spread": {"observed_sd": rate_sd,
                   "poisson_sd": math.sqrt(expected_rate / t_seconds)},
        "n_seeds": len(seeds),
    }


def convergence(params, seeds, expected):
    rows = []
    for t_s in CONVERGENCE_TIMES_S:
        one = [abs(run_one_hop(params, t_s * 1000, s)["rate"] - expected["one_hop_rate"])
               / expected["one_hop_rate"] for s in seeds]
        two = [abs(run_two_hop(params, t_s * 1000, s)["rate"] - expected["two_hop_rate"])
               / expected["two_hop_rate"] for s in seeds]
        rows.append({"T_s": t_s, "one_hop_err_pct": 100 * float(np.mean(one)),
                     "two_hop_err_pct": 100 * float(np.mean(two))})
    return rows


def print_scenario(r, grading_seed):
    n = r["n_seeds"]
    print(f"\n== {r['scenario']} ==")
    print(f"{'metric':<10}{'analytic':>10}{'seed ' + str(grading_seed):>14}{'err':>10}"
          f"{f'{n}-seed mean ± CI':>24}{'mean err':>11}{'in tol':>9}")
    q = r["rate"]
    print(f"{'rate':<10}{q['analytic']:>10.3f}{q['grading_seed']:>14.3f}{q['grading_seed_err_pct']:>9.2f}%"
          f"{q['mean']:>15.3f} ± {q['ci95']:<6.3f}{q['mean_err_pct']:>10.2f}%{q['within_tol']:>6}/{n}")
    f = r["fidelity"]
    print(f"{'fidelity':<10}{f['analytic']:>10.4f}{f['grading_seed']:>14.5f}{f['grading_seed_err']:>+10.1e}"
          f"{f['mean']:>15.4f} ± {f['ci95']:<6.4f}{f['mean_err']:>+11.1e}{f['within_tol']:>6}/{n}")
    w, s = r["worst_seed"], r["spread"]
    print(f"worst seed: {w['seed']} (rate {w['rate']:.3f}, {w['err_pct']:+.2f}%)")
    print(f"spread: observed SD {s['observed_sd']:.3f}, Poisson prediction {s['poisson_sd']:.3f}")


def main():
    with open("variant_params.json") as fh:
        params = json.load(fh)
    expected = params["reference"]["expected"]
    sim_time_ms = params["grading"]["sim_time_ms"]
    seeds = build_seeds(params)

    one = check_scenario("one_hop", run_one_hop, params, seeds, sim_time_ms,
                         expected["one_hop_rate"], params["physics"]["f_link"])
    two = check_scenario("two_hop", run_two_hop, params, seeds, sim_time_ms,
                         expected["two_hop_rate"], expected["two_hop_fidelity"])
    conv = convergence(params, seeds[:CONVERGENCE_N_SEEDS], expected)

    print(f"Seeds ({len(seeds)}): {seeds}")
    print_scenario(one, seeds[0])
    print_scenario(two, seeds[0])
    print(f"\n== Convergence (mean |relative rate error|, first {CONVERGENCE_N_SEEDS} seeds) ==")
    print(f"{'T (s)':>6}{'one-hop':>10}{'two-hop':>10}")
    for row in conv:
        print(f"{row['T_s']:>6}{row['one_hop_err_pct']:>9.2f}%{row['two_hop_err_pct']:>9.2f}%")

    out = {"seeds": seeds, "sim_time_ms": sim_time_ms, "one_hop": one, "two_hop": two,
           "convergence": {"seeds": seeds[:CONVERGENCE_N_SEEDS], "rows": conv}}
    with open("validation_results.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nWrote validation_results.json")


if __name__ == "__main__":
    main()
