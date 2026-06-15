"""
engine.py — Pure calculation module for the EDA TCO / Schedule Accelerator.
No Streamlit dependency. All inputs passed explicitly. See SPEC.md for formulas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def baseline_schedule(base_node_weeks: float) -> float:
    """
    Return the baseline schedule in weeks.

    Formula (SPEC §Formulas): baseline_weeks = base_node_weeks
    size_factor and clock_factor were removed; baseline is set directly.
    """
    return float(base_node_weeks)


def engineer_cost_per_week(fully_burdened_annual: float, team_size: int) -> float:
    """
    Return total team cost per week.

    Formula (SPEC §Formulas): eng_cost_wk = (fully_burdened_annual / 52) * team_size
    """
    return (fully_burdened_annual / 52.0) * team_size


def licensing_cost(
    licensing_mode: str,
    accelerated_weeks: float,
    baseline_weeks: float,
    team_size: int,
    token_cost_per_eng_week: float = 0,
    ai_token_multiplier: float = 1.0,
) -> float:
    """
    Return the marginal (incremental) licensing cost of choosing the AI-accelerated path.

    Formula (SPEC §Licensing):
        ela_or_sunk: return 0
            ELA customers treat licensing as a flat annual cost sunk at the
            company level; per-block decisions carry no marginal licensing cost.

        token: ai_token_cost   = accelerated_weeks * team_size
                                  * token_cost_per_eng_week * ai_token_multiplier
               baseline_token_cost = baseline_weeks * team_size * token_cost_per_eng_week
               return ai_token_cost - baseline_token_cost

    Result can be negative when schedule compression (fewer weeks * multiplier)
    outweighs the per-week token multiplier.
    """
    if licensing_mode == "ela_or_sunk":
        return 0.0
    elif licensing_mode == "token":
        ai_token_cost = (
            accelerated_weeks * team_size * token_cost_per_eng_week * ai_token_multiplier
        )
        baseline_token_cost = baseline_weeks * team_size * token_cost_per_eng_week
        return ai_token_cost - baseline_token_cost
    else:
        raise ValueError(f"Unknown licensing_mode: {licensing_mode!r}")


def baseline_cost(
    baseline_weeks: float,
    eng_cost_wk: float,
) -> dict[str, float]:
    """
    Return baseline path cost breakdown.

    Licensing is modeled as an incremental cost via licensing_cost() and is
    not included here — it nets out of the per-block decision correctly when
    added to accelerated_cost.

    Formula (SPEC §Formulas):
        baseline_labor = baseline_weeks * eng_cost_wk
        baseline_total = baseline_labor
    """
    labor = baseline_weeks * eng_cost_wk
    return {"labor": labor, "total": labor}


def accelerated_schedule(
    baseline_weeks: float,
    automatable_fraction: float,
    acceleration_factor: float,
) -> dict[str, float]:
    """
    Return accelerated schedule and weeks saved.

    Formula (SPEC §Formulas):
        automatable_weeks = baseline_weeks * automatable_fraction
        non_auto_weeks    = baseline_weeks * (1 - automatable_fraction)
        accel_auto_weeks  = automatable_weeks / acceleration_factor
        accelerated_weeks = non_auto_weeks + accel_auto_weeks
        weeks_saved       = baseline_weeks - accelerated_weeks
    """
    automatable_weeks = baseline_weeks * automatable_fraction
    non_auto_weeks = baseline_weeks * (1.0 - automatable_fraction)
    accel_auto_weeks = automatable_weeks / acceleration_factor
    accelerated_weeks = non_auto_weeks + accel_auto_weeks
    weeks_saved = baseline_weeks - accelerated_weeks
    return {"accelerated_weeks": accelerated_weeks, "weeks_saved": weeks_saved}


def accelerated_cost(
    accelerated_weeks: float,
    eng_cost_wk: float,
    ai_licensing: float,
    parallel_gpus: int,
    compute_hours: float,
    cloud_rate_per_gpu_hr: float,
) -> dict[str, float]:
    """
    Return accelerated path cost breakdown.

    ai_licensing is the output of licensing_cost() and may be negative when
    schedule compression dominates the token multiplier.

    Formula (SPEC §Formulas):
        accel_labor  = accelerated_weeks * eng_cost_wk
        compute_cost = parallel_gpus * compute_hours * cloud_rate_per_gpu_hr
        accel_total  = accel_labor + compute_cost + ai_licensing
    """
    labor = accelerated_weeks * eng_cost_wk
    compute = parallel_gpus * compute_hours * cloud_rate_per_gpu_hr
    return {
        "labor": labor,
        "compute": compute,
        "ai_licensing": ai_licensing,
        "total": labor + compute + ai_licensing,
    }


def acceleration_value(weeks_saved: float, value_per_week: float) -> float:
    """
    Return the dollar value of time saved.

    Formula (SPEC §Formulas): accel_value = weeks_saved * value_per_week
    """
    return weeks_saved * value_per_week


def net_benefit(
    baseline_total: float,
    accel_total: float,
    accel_value: float,
) -> float:
    """
    Return net economic benefit of the AI-accelerated path.

    Formula (SPEC §Formulas): net_benefit = baseline_total - accel_total + accel_value
    """
    return baseline_total - accel_total + accel_value


def breakeven_compute(
    baseline_total: float,
    accel_labor: float,
    accel_ai_licensing: float,
    accel_value: float,
) -> float:
    """
    Return the maximum compute spend at which the AI path is still net-positive.

    Formula (SPEC §Formulas):
        breakeven_compute = baseline_total - accel_labor - accel_ai_licensing + accel_value

    Derived by setting net_benefit = 0 and solving for compute_cost.
    accel_ai_licensing is the marginal licensing cost from licensing_cost() and
    may be negative, which widens the break-even budget.
    """
    return baseline_total - accel_labor - accel_ai_licensing + accel_value


def ppa_lifecycle_saving(
    deployed_units: int,
    power_per_unit_w: float,
    leakage_reduction_pct: float,
    hours_per_year: float,
    electricity_cost_per_kwh: float,
    years: int = 3,
) -> dict[str, float]:
    """
    Return annual and lifecycle power cost savings from PPA improvement.

    Formula (SPEC §Formulas):
        annual_power_saving  = deployed_units * power_per_unit_w
                               * leakage_reduction_pct * hours_per_year
                               * electricity_cost_per_kwh / 1000.0
        lifecycle_ppa_saving = annual_power_saving * years
    """
    annual = (
        deployed_units
        * power_per_unit_w
        * leakage_reduction_pct
        * hours_per_year
        * electricity_cost_per_kwh
        / 1000.0
    )
    return {"annual": annual, "lifecycle": annual * years}


def sensitivity_grid(
    value_per_week_range: list[float],
    cloud_rate_range: list[float],
    base_node_weeks: float,
    team_size: int,
    fully_burdened_annual: float,
    automatable_fraction: float,
    acceleration_factor: float,
    parallel_gpus: int,
    compute_hours: float,
    licensing_mode: str,
    token_cost_per_eng_week: float = 0,
    ai_token_multiplier: float = 1.0,
) -> pd.DataFrame:
    """
    Return a DataFrame of net_benefit values across value_per_week (rows)
    by cloud_rate_per_gpu_hr (columns).

    Default ranges (SPEC confirmed 2026-05-28):
        value_per_week_range : [50_000, 100_000, 250_000, 500_000, 1_000_000, 2_000_000]
        cloud_rate_range     : [2, 3, 5, 8, 12]
    """
    eng_cost_wk = engineer_cost_per_week(fully_burdened_annual, team_size)
    baseline_weeks = baseline_schedule(base_node_weeks)
    bc = baseline_cost(baseline_weeks, eng_cost_wk)
    sched = accelerated_schedule(baseline_weeks, automatable_fraction, acceleration_factor)
    ai_lic = licensing_cost(
        licensing_mode,
        sched["accelerated_weeks"],
        baseline_weeks,
        team_size,
        token_cost_per_eng_week,
        ai_token_multiplier,
    )

    rows = []
    for vpw in value_per_week_range:
        row = {}
        for rate in cloud_rate_range:
            ac = accelerated_cost(
                sched["accelerated_weeks"],
                eng_cost_wk,
                ai_lic,
                parallel_gpus,
                compute_hours,
                rate,
            )
            av = acceleration_value(sched["weeks_saved"], vpw)
            nb = net_benefit(bc["total"], ac["total"], av)
            row[rate] = nb
        rows.append(row)

    df = pd.DataFrame(rows, index=value_per_week_range)
    df.index.name = "value_per_week"
    df.columns.name = "cloud_rate_per_gpu_hr"
    return df


def compute_sweep(
    breakeven: float,
    baseline_total: float,
    accel_labor: float,
    accel_ai_licensing: float,
    accel_value: float,
    n_points: int = 100,
) -> pd.DataFrame:
    """
    Return a DataFrame sweeping compute_cost as a scalar from $0 to 2×breakeven,
    holding all other parameters constant.

    Columns: compute_cost, net_benefit
    Formula: net_benefit = baseline_total - (accel_labor + compute_cost + accel_ai_licensing) + accel_value

    The sweep asks "what if you spent $X on compute" — it does not re-derive
    how that spend is allocated across GPUs, hours, or rates.
    """
    max_spend = 2.0 * breakeven if breakeven > 0 else 1.0
    compute_costs = np.linspace(0.0, max_spend, n_points)
    nb_values = (
        baseline_total - (accel_labor + compute_costs + accel_ai_licensing) + accel_value
    )
    return pd.DataFrame({"compute_cost": compute_costs, "net_benefit": nb_values})
