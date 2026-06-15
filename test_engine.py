"""
test_engine.py — Unit tests for engine.py.
Run with: python -m pytest test_engine.py -v
"""

import pytest
import pandas as pd
import numpy as np

from engine import (
    baseline_schedule,
    engineer_cost_per_week,
    licensing_cost,
    baseline_cost,
    accelerated_schedule,
    accelerated_cost,
    acceleration_value,
    net_benefit,
    breakeven_compute,
    ppa_lifecycle_saving,
    sensitivity_grid,
    compute_sweep,
)


# ---------------------------------------------------------------------------
# baseline_schedule
# ---------------------------------------------------------------------------

def test_baseline_schedule_returns_base_node_weeks():
    assert baseline_schedule(12.0) == 12.0


def test_baseline_schedule_float_passthrough():
    assert baseline_schedule(9.5) == 9.5


def test_baseline_schedule_node_presets():
    assert baseline_schedule(9.0) == 9.0   # 5nm
    assert baseline_schedule(12.0) == 12.0  # 3nm
    assert baseline_schedule(16.0) == 16.0  # 2nm


# ---------------------------------------------------------------------------
# engineer_cost_per_week
# ---------------------------------------------------------------------------

def test_engineer_cost_per_week_defaults():
    expected = (300_000 / 52) * 5
    assert abs(engineer_cost_per_week(300_000, 5) - expected) < 0.01


def test_engineer_cost_per_week_team_of_one():
    # (52_000 / 52) * 1 = 1_000
    assert abs(engineer_cost_per_week(52_000, 1) - 1_000.0) < 0.01


def test_engineer_cost_per_week_scales_linearly_with_team():
    single = engineer_cost_per_week(300_000, 1)
    five = engineer_cost_per_week(300_000, 5)
    assert abs(five - single * 5) < 0.01


# ---------------------------------------------------------------------------
# licensing_cost
# ---------------------------------------------------------------------------

def test_licensing_cost_ela_or_sunk_is_zero():
    result = licensing_cost("ela_or_sunk", 8.4, 12.0, 5, 5_000, 4.0)
    assert result == 0.0


def test_licensing_cost_ela_or_sunk_ignores_token_params():
    # Should return 0 regardless of token_cost and multiplier values
    assert licensing_cost("ela_or_sunk", 8.4, 12.0, 5, 99_999, 99.0) == 0.0


def test_licensing_cost_token_positive():
    # Default values from spec: accel=8.4, baseline=12, team=5, cost=5000, mult=4
    # ai_token = 8.4 * 5 * 5000 * 4 = 840_000
    # baseline_token = 12 * 5 * 5000 = 300_000
    # result = 540_000
    result = licensing_cost("token", 8.4, 12.0, 5, 5_000, 4.0)
    assert abs(result - 540_000.0) < 0.01


def test_licensing_cost_token_negative_when_compression_dominates():
    # multiplier=1.0 → accel path spends fewer weeks, net cost is negative
    # accel=8.4, baseline=12, team=5, cost=5000, mult=1.0
    # ai_token = 8.4 * 5 * 5000 * 1.0 = 210_000
    # baseline_token = 12 * 5 * 5000 = 300_000
    # result = -90_000
    result = licensing_cost("token", 8.4, 12.0, 5, 5_000, 1.0)
    assert abs(result - (-90_000.0)) < 0.01


def test_licensing_cost_token_zero_when_perfectly_offset():
    # accel=6, baseline=12, team=5, cost=1000, mult=2.0
    # ai_token = 6 * 5 * 1000 * 2 = 60_000
    # baseline_token = 12 * 5 * 1000 = 60_000
    # result = 0
    result = licensing_cost("token", 6.0, 12.0, 5, 1_000, 2.0)
    assert abs(result) < 1e-9


def test_licensing_cost_token_zero_cost_is_zero():
    result = licensing_cost("token", 8.4, 12.0, 5, 0, 4.0)
    assert result == 0.0


def test_licensing_cost_invalid_mode_raises():
    with pytest.raises(ValueError, match="Unknown licensing_mode"):
        licensing_cost("per_seat", 8.4, 12.0, 5, 5_000, 4.0)


# ---------------------------------------------------------------------------
# baseline_cost
# ---------------------------------------------------------------------------

def test_baseline_cost_keys():
    eng_cost_wk = engineer_cost_per_week(300_000, 5)
    result = baseline_cost(12.0, eng_cost_wk)
    assert set(result.keys()) == {"labor", "total"}


def test_baseline_cost_values():
    # 10 weeks, $10k/wk eng cost
    result = baseline_cost(10.0, 10_000.0)
    assert result["labor"] == 100_000.0
    assert result["total"] == 100_000.0


def test_baseline_cost_total_equals_labor():
    eng_cost_wk = engineer_cost_per_week(300_000, 5)
    result = baseline_cost(12.0, eng_cost_wk)
    assert abs(result["total"] - result["labor"]) < 1e-9


def test_baseline_cost_scales_with_weeks():
    result_10 = baseline_cost(10.0, 5_000.0)
    result_20 = baseline_cost(20.0, 5_000.0)
    assert abs(result_20["total"] - 2 * result_10["total"]) < 1e-9


# ---------------------------------------------------------------------------
# accelerated_schedule
# ---------------------------------------------------------------------------

def test_accelerated_schedule_keys():
    result = accelerated_schedule(12.0, 0.40, 4.0)
    assert set(result.keys()) == {"accelerated_weeks", "weeks_saved"}


def test_accelerated_schedule_default_values():
    # baseline=12, auto_frac=0.40, accel=4.0
    # automatable=4.8, non_auto=7.2, accel_auto=1.2
    # accelerated=8.4, saved=3.6
    result = accelerated_schedule(12.0, 0.40, 4.0)
    assert abs(result["accelerated_weeks"] - 8.4) < 1e-9
    assert abs(result["weeks_saved"] - 3.6) < 1e-9


def test_accelerated_schedule_zero_fraction():
    result = accelerated_schedule(12.0, 0.0, 4.0)
    assert result["accelerated_weeks"] == 12.0
    assert result["weeks_saved"] == 0.0


def test_accelerated_schedule_full_fraction():
    result = accelerated_schedule(12.0, 1.0, 4.0)
    assert abs(result["accelerated_weeks"] - 3.0) < 1e-9
    assert abs(result["weeks_saved"] - 9.0) < 1e-9


def test_accelerated_schedule_weeks_saved_equals_difference():
    result = accelerated_schedule(12.0, 0.40, 4.0)
    assert abs(result["weeks_saved"] - (12.0 - result["accelerated_weeks"])) < 1e-9


def test_accelerated_schedule_higher_acceleration_saves_more():
    slow = accelerated_schedule(12.0, 0.40, 2.0)
    fast = accelerated_schedule(12.0, 0.40, 10.0)
    assert fast["weeks_saved"] > slow["weeks_saved"]


# ---------------------------------------------------------------------------
# accelerated_cost
# ---------------------------------------------------------------------------

def test_accelerated_cost_keys():
    result = accelerated_cost(8.4, 10_000, 0.0, 64, 500, 3.0)
    assert set(result.keys()) == {"labor", "compute", "ai_licensing", "total"}


def test_accelerated_cost_values():
    # 10 weeks, $10k/wk, ai_licensing=$12k, 10 GPUs, 100 hrs, $2/hr
    # labor   = 10 * 10_000 = 100_000
    # compute = 10 * 100 * 2.0 = 2_000
    # ai_licensing = 12_000
    # total   = 114_000
    result = accelerated_cost(10.0, 10_000, 12_000, 10, 100, 2.0)
    assert result["labor"] == 100_000.0
    assert result["compute"] == 2_000.0
    assert result["ai_licensing"] == 12_000.0
    assert result["total"] == 114_000.0


def test_accelerated_cost_zero_licensing():
    result = accelerated_cost(10.0, 10_000, 0.0, 10, 100, 2.0)
    assert result["ai_licensing"] == 0.0
    assert result["total"] == result["labor"] + result["compute"]


def test_accelerated_cost_negative_licensing_reduces_total():
    result = accelerated_cost(10.0, 10_000, -5_000, 10, 100, 2.0)
    assert result["ai_licensing"] == -5_000.0
    assert result["total"] == 97_000.0


def test_accelerated_cost_total_is_sum():
    result = accelerated_cost(8.4, 10_000, 15_000.0, 64, 500, 3.0)
    expected = result["labor"] + result["compute"] + result["ai_licensing"]
    assert abs(result["total"] - expected) < 0.01


# ---------------------------------------------------------------------------
# acceleration_value
# ---------------------------------------------------------------------------

def test_acceleration_value_default():
    # 3.6 weeks * $250_000/wk = $900_000
    assert acceleration_value(3.6, 250_000) == 900_000.0


def test_acceleration_value_zero_weeks():
    assert acceleration_value(0.0, 250_000) == 0.0


def test_acceleration_value_zero_value():
    assert acceleration_value(5.0, 0.0) == 0.0


# ---------------------------------------------------------------------------
# net_benefit
# ---------------------------------------------------------------------------

def test_net_benefit_positive():
    assert net_benefit(500_000, 400_000, 200_000) == 300_000.0


def test_net_benefit_negative():
    assert net_benefit(100_000, 500_000, 0) == -400_000.0


def test_net_benefit_zero():
    assert net_benefit(200_000, 300_000, 100_000) == 0.0


# ---------------------------------------------------------------------------
# breakeven_compute
# ---------------------------------------------------------------------------

def test_breakeven_compute_formula():
    # 500_000 - 200_000 - 100_000 + 150_000 = 350_000
    result = breakeven_compute(500_000, 200_000, 100_000, 150_000)
    assert result == 350_000.0


def test_breakeven_compute_negative_ai_licensing_widens_budget():
    # negative ai_licensing subtracts a negative → increases breakeven
    result_zero = breakeven_compute(500_000, 200_000, 0, 150_000)
    result_neg = breakeven_compute(500_000, 200_000, -50_000, 150_000)
    assert result_neg > result_zero


def test_breakeven_compute_makes_net_benefit_zero():
    baseline_total = 500_000.0
    accel_labor = 200_000.0
    accel_ai_licensing = 100_000.0
    accel_value = 150_000.0
    be = breakeven_compute(baseline_total, accel_labor, accel_ai_licensing, accel_value)
    nb = net_benefit(baseline_total, accel_labor + be + accel_ai_licensing, accel_value)
    assert abs(nb) < 1e-9


# ---------------------------------------------------------------------------
# ppa_lifecycle_saving
# ---------------------------------------------------------------------------

def test_ppa_lifecycle_saving_keys():
    result = ppa_lifecycle_saving(100_000, 300, 0.08, 8760, 0.10)
    assert set(result.keys()) == {"annual", "lifecycle"}


def test_ppa_lifecycle_saving_default_values():
    # 100_000 units * 300 W * 0.08 * 8760 hrs * $0.10/kWh / 1000 = $2_102_400
    result = ppa_lifecycle_saving(100_000, 300, 0.08, 8760, 0.10)
    expected_annual = 100_000 * 300 * 0.08 * 8760 * 0.10 / 1000.0
    assert abs(result["annual"] - expected_annual) < 0.01
    assert abs(result["lifecycle"] - expected_annual * 3) < 0.01


def test_ppa_lifecycle_saving_custom_years():
    result_3 = ppa_lifecycle_saving(100_000, 300, 0.08, 8760, 0.10, years=3)
    result_5 = ppa_lifecycle_saving(100_000, 300, 0.08, 8760, 0.10, years=5)
    assert abs(result_5["lifecycle"] - result_3["annual"] * 5) < 0.01


def test_ppa_lifecycle_saving_zero_reduction():
    result = ppa_lifecycle_saving(100_000, 300, 0.0, 8760, 0.10)
    assert result["annual"] == 0.0
    assert result["lifecycle"] == 0.0


def test_ppa_lifecycle_saving_lifecycle_equals_annual_times_years():
    result = ppa_lifecycle_saving(100_000, 300, 0.08, 8760, 0.10, years=7)
    assert abs(result["lifecycle"] - result["annual"] * 7) < 0.01


# ---------------------------------------------------------------------------
# sensitivity_grid
# ---------------------------------------------------------------------------

VALUE_RANGE = [50_000, 100_000, 250_000, 500_000, 1_000_000, 2_000_000]
RATE_RANGE = [2, 3, 5, 8, 12]

GRID_FIXED = dict(
    base_node_weeks=12.0,
    team_size=5,
    fully_burdened_annual=300_000,
    automatable_fraction=0.40,
    acceleration_factor=4.0,
    parallel_gpus=64,
    compute_hours=500,
    licensing_mode="ela_or_sunk",
)


def test_sensitivity_grid_shape():
    df = sensitivity_grid(VALUE_RANGE, RATE_RANGE, **GRID_FIXED)
    assert df.shape == (6, 5)


def test_sensitivity_grid_index():
    df = sensitivity_grid(VALUE_RANGE, RATE_RANGE, **GRID_FIXED)
    assert list(df.index) == VALUE_RANGE


def test_sensitivity_grid_columns():
    df = sensitivity_grid(VALUE_RANGE, RATE_RANGE, **GRID_FIXED)
    assert list(df.columns) == RATE_RANGE


def test_sensitivity_grid_returns_dataframe():
    df = sensitivity_grid(VALUE_RANGE, RATE_RANGE, **GRID_FIXED)
    assert isinstance(df, pd.DataFrame)


def test_sensitivity_grid_higher_value_per_week_higher_net_benefit():
    df = sensitivity_grid(VALUE_RANGE, RATE_RANGE, **GRID_FIXED)
    for col in df.columns:
        assert df[col].is_monotonic_increasing, (
            f"net_benefit not monotonically increasing with value_per_week at rate={col}"
        )


def test_sensitivity_grid_higher_cloud_rate_lower_net_benefit():
    df = sensitivity_grid(VALUE_RANGE, RATE_RANGE, **GRID_FIXED)
    for idx in df.index:
        assert df.loc[idx].is_monotonic_decreasing, (
            f"net_benefit not monotonically decreasing with cloud_rate at vpw={idx}"
        )


def test_sensitivity_grid_token_mode_positive_licensing_shifts_down():
    # Token mode with high multiplier → positive licensing cost → net_benefit lower than ELA
    ela_df = sensitivity_grid(VALUE_RANGE, RATE_RANGE, **GRID_FIXED)
    token_df = sensitivity_grid(
        VALUE_RANGE, RATE_RANGE,
        **{**GRID_FIXED, "licensing_mode": "token",
           "token_cost_per_eng_week": 5_000, "ai_token_multiplier": 4.0},
    )
    # Every cell in token mode should be lower (positive licensing cost adds to accel_total)
    assert (token_df.values < ela_df.values).all()


# ---------------------------------------------------------------------------
# compute_sweep
# ---------------------------------------------------------------------------

def test_compute_sweep_shape():
    df = compute_sweep(500_000, 600_000, 200_000, 100_000, 150_000, n_points=100)
    assert df.shape == (100, 2)
    assert set(df.columns) == {"compute_cost", "net_benefit"}


def test_compute_sweep_starts_at_zero():
    df = compute_sweep(500_000, 600_000, 200_000, 100_000, 150_000)
    assert df["compute_cost"].iloc[0] == 0.0


def test_compute_sweep_ends_at_2x_breakeven():
    be = 500_000.0
    df = compute_sweep(be, 600_000, 200_000, 100_000, 150_000)
    assert abs(df["compute_cost"].iloc[-1] - 2 * be) < 0.01


def test_compute_sweep_net_benefit_is_monotonically_decreasing():
    df = compute_sweep(500_000, 600_000, 200_000, 100_000, 150_000)
    diffs = df["net_benefit"].diff().dropna()
    assert (diffs < 0).all()


def test_compute_sweep_net_benefit_at_zero_compute():
    baseline_total = 600_000.0
    accel_labor = 200_000.0
    accel_ai_licensing = 100_000.0
    accel_value = 150_000.0
    df = compute_sweep(500_000, baseline_total, accel_labor, accel_ai_licensing, accel_value)
    expected_at_zero = baseline_total - (accel_labor + 0 + accel_ai_licensing) + accel_value
    assert abs(df["net_benefit"].iloc[0] - expected_at_zero) < 0.01


def test_compute_sweep_breakeven_is_zero_crossing():
    be = 350_000.0
    df = compute_sweep(be, 500_000, 200_000, 100_000, 150_000)
    closest_idx = (df["compute_cost"] - be).abs().idxmin()
    assert abs(df.loc[closest_idx, "net_benefit"]) < 5_000  # within $5k (discrete grid)


def test_compute_sweep_returns_dataframe():
    df = compute_sweep(500_000, 600_000, 200_000, 100_000, 150_000)
    assert isinstance(df, pd.DataFrame)


def test_compute_sweep_negative_ai_licensing_shifts_net_benefit_up():
    # Negative ai_licensing (schedule compression dominates) boosts net_benefit
    df_zero = compute_sweep(500_000, 600_000, 200_000, 0, 150_000)
    df_neg = compute_sweep(500_000, 600_000, 200_000, -50_000, 150_000)
    assert (df_neg["net_benefit"].values > df_zero["net_benefit"].values).all()
