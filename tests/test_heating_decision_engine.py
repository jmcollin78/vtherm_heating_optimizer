from datetime import datetime, timedelta

from appdaemon.apps.vtherm_heating_optimizer import (
    HeatingDecisionEngine,
    HeatingSource,
    OptimizerConfig,
    OptimizerInputs,
)


def _base_inputs(**overrides):
    data = {
        "indoor_temp_c": 19.0,
        "setpoint_temp_c": 20.0,
        "electricity_price_eur_kwh": 0.20,
        "pv_power_w": 0.0,
        "battery_soc_pct": 50.0,
        "battery_power_w": 0.0,
        "net_consumption_w": 0.0,
    }
    data.update(overrides)
    return OptimizerInputs(**data)


def test_prefers_ac_when_cheaper_than_pellet():
    engine = HeatingDecisionEngine(OptimizerConfig(ac_cop=3.0))
    result = engine.decide(_base_inputs(electricity_price_eur_kwh=0.18))
    assert result.source == HeatingSource.AC


def test_invalid_price_uses_default_electricity_price():
    engine = HeatingDecisionEngine(OptimizerConfig(default_electricity_price_eur_kwh=0.21))
    result = engine.decide(_base_inputs(electricity_price_eur_kwh=None))
    assert result.electricity_cost_eur_kwh == 0.21


def test_hysteresis_stops_heating_close_to_setpoint():
    engine = HeatingDecisionEngine()
    result = engine.decide(_base_inputs(indoor_temp_c=19.95, setpoint_temp_c=20.0))
    assert result.source == HeatingSource.NONE


def test_anti_cycling_keeps_current_source_when_switch_too_early():
    engine = HeatingDecisionEngine(
        OptimizerConfig(min_on_seconds=600, min_off_seconds=600)
    )
    now = datetime.utcnow()

    engine.active_source = HeatingSource.PELLET
    engine.last_switch_at = now - timedelta(seconds=120)

    result = engine.decide(_base_inputs(electricity_price_eur_kwh=0.12), now=now)
    assert result.source == HeatingSource.PELLET
    assert "anti-cycling" in result.reason


def test_radiator_fallback_when_pellet_unavailable_and_ac_unavailable():
    engine = HeatingDecisionEngine(OptimizerConfig(ac_cop=0.0, pellet_bag_weight_kg=0.0))
    result = engine.decide(
        _base_inputs(
        )
    )
    assert result.source == HeatingSource.RADIATOR
