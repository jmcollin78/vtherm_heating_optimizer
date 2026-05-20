from datetime import datetime, timedelta

from appdaemon.apps.vtherm_heating_optimizer import (
    HeatingDecisionEngine,
    HeatingSource,
    OptimizerConfig,
    OptimizerInputs,
    VThermHeatingOptimizer,
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
    engine = HeatingDecisionEngine(
        OptimizerConfig(default_electricity_price_eur_kwh=0.21)
    )
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
    engine = HeatingDecisionEngine(
        OptimizerConfig(ac_cop=0.0, pellet_bag_weight_kg=0.0)
    )
    result = engine.decide(_base_inputs())
    assert result.source == HeatingSource.RADIATOR


def test_persistent_notification_sent_on_equipment_change():
    app = VThermHeatingOptimizer()
    app.engine = HeatingDecisionEngine(
        OptimizerConfig(min_on_seconds=0, min_off_seconds=0)
    )
    app.entities = {
        "electricity_price": "sensor.tempo_price",
        "pv_power": "sensor.pv_power",
        "battery_soc": "sensor.battery_soc",
        "battery_power": "sensor.battery_power",
        "net_consumption": "sensor.net_consumption",
        "indoor_temp": "sensor.indoor_temp",
        "pellet_climate": "climate.vtherm_poele",
        "ac_climate": "climate.clim_salon",
        "radiator_climate": "climate.thermostat_sam1",
    }
    app.dry_run = True

    service_calls = []

    def _fake_get_state(entity_id, attribute=None):
        if attribute == "temperature":
            return 20.0
        if attribute == "current_temperature":
            return 19.0
        values = {
            "sensor.tempo_price": "0.12",
            "sensor.pv_power": "0",
            "sensor.battery_soc": "50",
            "sensor.battery_power": "0",
            "sensor.net_consumption": "0",
            "sensor.indoor_temp": "19.0",
        }
        return values.get(entity_id)

    app.get_state = _fake_get_state
    app.log = lambda *args, **kwargs: None

    def _fake_call_service(service, **kwargs):
        service_calls.append((service, kwargs))

    app.call_service = _fake_call_service

    app._run_cycle({})

    notification_calls = [
        call for call in service_calls if call[0] == "persistent_notification/create"
    ]
    assert len(notification_calls) == 1
    service_name, payload = notification_calls[0]
    assert service_name == "persistent_notification/create"
    assert payload["title"] == "vtherm_heating_optimizer - Changement d'état chauffage"
    assert "🔥" in payload["message"]
    assert "a été allumé" in payload["message"]
