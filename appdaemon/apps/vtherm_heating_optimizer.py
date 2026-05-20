"""VTherm Heating Optimizer AppDaemon prototype.

This module implements step 1 of the execution plan: a fast AppDaemon prototype
that computes heating source costs and selects one source with hysteresis and
anti-cycling constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

try:
    import appdaemon.plugins.hass.hassapi as hass
except ImportError:  # pragma: no cover - only used outside AppDaemon runtime

    class _HassBase:
        """Minimal fallback base class for local tests."""

    class hass:  # type: ignore
        Hass = _HassBase


class HeatingSource(str, Enum):
    NONE = "none"
    PELLET = "pellet"
    AC = "ac"
    RADIATOR = "radiator"


@dataclass(frozen=True)
class OptimizerConfig:
    cycle_seconds: int = 60
    hysteresis_on_delta_c: float = 0.4
    hysteresis_off_delta_c: float = 0.1
    emergency_delta_c: float = 1.5
    min_on_seconds: int = 600
    min_off_seconds: int = 600
    battery_support_threshold_w: float = 500.0
    solar_support_threshold_w: float = 500.0
    ac_cop: float = 3.0
    pellet_kwh_per_kg: float = 4.8
    pellet_efficiency: float = 0.85
    default_tempo_prices: Dict[str, float] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.default_tempo_prices is None:
            object.__setattr__(
                self,
                "default_tempo_prices",
                {
                    "blue_hc": 0.10,
                    "blue_hp": 0.13,
                    "white_hc": 0.13,
                    "white_hp": 0.16,
                    "red_hc": 0.15,
                    "red_hp": 0.75,
                },
            )


@dataclass(frozen=True)
class OptimizerInputs:
    indoor_temp_c: float
    setpoint_temp_c: float
    tempo_color: str
    tempo_period: str
    tempo_price_eur_kwh: Optional[float]
    pv_power_w: float
    battery_soc_pct: float
    battery_power_w: float
    surplus_solar_w: float
    pellet_bag_price_eur: float
    pellet_bag_weight_kg: float


@dataclass(frozen=True)
class DecisionResult:
    source: HeatingSource
    electricity_cost_eur_kwh: float
    pellet_cost_eur_kwh: float
    ac_cost_eur_kwh: float
    radiator_cost_eur_kwh: float
    reason: str


class HeatingDecisionEngine:
    """Pure decision engine, independent from AppDaemon runtime."""

    def __init__(self, config: Optional[OptimizerConfig] = None) -> None:
        self.config = config or OptimizerConfig()
        self.active_source = HeatingSource.NONE
        self.last_switch_at: Optional[datetime] = None

    def _is_red_peak(self, tempo_color: str, tempo_period: str) -> bool:
        return tempo_color.lower() == "red" and tempo_period.lower() == "hp"

    def _electricity_cost(self, data: OptimizerInputs) -> float:
        if data.tempo_price_eur_kwh is not None and data.tempo_price_eur_kwh > 0:
            return data.tempo_price_eur_kwh

        key = f"{data.tempo_color.lower()}_{data.tempo_period.lower()}"
        return self.config.default_tempo_prices.get(
            key, self.config.default_tempo_prices["white_hp"]
        )

    def _pellet_cost(self, data: OptimizerInputs) -> float:
        useful_kwh = (
            data.pellet_bag_weight_kg
            * self.config.pellet_kwh_per_kg
            * self.config.pellet_efficiency
        )
        if useful_kwh <= 0:
            return float("inf")
        return data.pellet_bag_price_eur / useful_kwh

    def _has_support_energy(self, data: OptimizerInputs) -> bool:
        return (
            data.surplus_solar_w >= self.config.solar_support_threshold_w
            or data.battery_power_w >= self.config.battery_support_threshold_w
        )

    def _heat_needed(self, data: OptimizerInputs) -> bool:
        if self.active_source == HeatingSource.NONE:
            return data.indoor_temp_c < (
                data.setpoint_temp_c - self.config.hysteresis_on_delta_c
            )
        return data.indoor_temp_c < (
            data.setpoint_temp_c - self.config.hysteresis_off_delta_c
        )

    def _can_switch(self, now: datetime) -> bool:
        if self.last_switch_at is None:
            return True
        elapsed = (now - self.last_switch_at).total_seconds()
        if self.active_source == HeatingSource.NONE:
            return elapsed >= self.config.min_off_seconds
        return elapsed >= self.config.min_on_seconds

    def decide(
        self, data: OptimizerInputs, now: Optional[datetime] = None
    ) -> DecisionResult:
        now = now or datetime.utcnow()

        electricity_cost = self._electricity_cost(data)
        pellet_cost = self._pellet_cost(data)
        ac_cost = (
            electricity_cost / self.config.ac_cop
            if self.config.ac_cop > 0
            else float("inf")
        )
        radiator_cost = electricity_cost
        red_peak = self._is_red_peak(data.tempo_color, data.tempo_period)

        if not self._heat_needed(data):
            return DecisionResult(
                source=HeatingSource.NONE,
                electricity_cost_eur_kwh=electricity_cost,
                pellet_cost_eur_kwh=pellet_cost,
                ac_cost_eur_kwh=ac_cost,
                radiator_cost_eur_kwh=radiator_cost,
                reason="indoor temperature above hysteresis threshold",
            )

        support_energy = self._has_support_energy(data)
        ac_allowed = not red_peak
        radiator_allowed = not red_peak

        if red_peak and data.indoor_temp_c < (
            data.setpoint_temp_c - self.config.emergency_delta_c
        ):
            radiator_allowed = True

        preferred = HeatingSource.PELLET
        reason = "pellet as base load"

        if ac_allowed and (ac_cost < pellet_cost or support_energy):
            preferred = HeatingSource.AC
            reason = "ac selected by lower cost or support energy"
        elif radiator_allowed and preferred == HeatingSource.NONE:
            preferred = HeatingSource.RADIATOR
            reason = "radiator as fallback"

        if preferred == HeatingSource.PELLET:
            if not ac_allowed and not radiator_allowed:
                reason = "red peak keeps electric sources disabled"
            if pellet_cost == float("inf") and radiator_allowed:
                preferred = HeatingSource.RADIATOR
                reason = "pellet cost unavailable, radiator fallback"

        if preferred == HeatingSource.NONE and radiator_allowed:
            preferred = HeatingSource.RADIATOR
            reason = "radiator as emergency fallback"

        if preferred != self.active_source and not self._can_switch(now):
            preferred = self.active_source
            reason = "anti-cycling active, keeping current source"

        return DecisionResult(
            source=preferred,
            electricity_cost_eur_kwh=electricity_cost,
            pellet_cost_eur_kwh=pellet_cost,
            ac_cost_eur_kwh=ac_cost,
            radiator_cost_eur_kwh=radiator_cost,
            reason=reason,
        )

    def commit(self, source: HeatingSource, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        if source != self.active_source:
            self.active_source = source
            self.last_switch_at = now


class VThermHeatingOptimizer(hass.Hass):
    """AppDaemon app that applies the decision engine to Home Assistant climates."""

    config: OptimizerConfig
    engine: HeatingDecisionEngine
    entities: Dict[str, str]
    dry_run: bool

    def initialize(self) -> None:
        self.config = OptimizerConfig(
            cycle_seconds=int(self.args.get("cycle_seconds", 60)),
            hysteresis_on_delta_c=float(self.args.get("hysteresis_on_delta_c", 0.4)),
            hysteresis_off_delta_c=float(self.args.get("hysteresis_off_delta_c", 0.1)),
            emergency_delta_c=float(self.args.get("emergency_delta_c", 1.5)),
            min_on_seconds=int(self.args.get("min_on_seconds", 600)),
            min_off_seconds=int(self.args.get("min_off_seconds", 600)),
            battery_support_threshold_w=float(
                self.args.get("battery_support_threshold_w", 500.0)
            ),
            solar_support_threshold_w=float(
                self.args.get("solar_support_threshold_w", 500.0)
            ),
            ac_cop=float(self.args.get("ac_cop", 3.0)),
            pellet_kwh_per_kg=float(self.args.get("pellet_kwh_per_kg", 4.8)),
            pellet_efficiency=float(self.args.get("pellet_efficiency", 0.85)),
        )
        self.engine = HeatingDecisionEngine(self.config)

        self.entities = {
            "tempo_color": self.args.get("tempo_color_entity", "sensor.tempo_color"),
            "tempo_period": self.args.get("tempo_period_entity", "sensor.tempo_period"),
            "tempo_price": self.args.get("tempo_price_entity", "sensor.tempo_price"),
            "pv_power": self.args.get("pv_power_entity", "sensor.pv_power"),
            "battery_soc": self.args.get("battery_soc_entity", "sensor.battery_soc"),
            "battery_power": self.args.get(
                "battery_power_entity", "sensor.battery_power"
            ),
            "surplus_solar": self.args.get(
                "surplus_solar_entity", "sensor.surplus_solar"
            ),
            "indoor_temp": self.args.get("indoor_temp_entity", "sensor.temp_salon"),
            "setpoint": self.args.get(
                "setpoint_temp_entity", "input_number.vtherm_target_temp"
            ),
            "pellet_bag_price": self.args.get(
                "pellet_bag_price_entity", "input_number.pellet_bag_price_eur"
            ),
            "pellet_bag_weight": self.args.get(
                "pellet_bag_weight_entity", "input_number.pellet_bag_weight_kg"
            ),
            "pellet_climate": self.args.get(
                "pellet_climate_entity", "climate.vtherm_poele"
            ),
            "ac_climate": self.args.get("ac_climate_entity", "climate.clim_salon"),
            "radiator_climate": self.args.get(
                "radiator_climate_entity", "climate.thermostat_sam1"
            ),
        }

        self.dry_run = bool(self.args.get("dry_run", True))
        self.run_every(self._run_cycle, "now", self.config.cycle_seconds)
        self.log("VTherm Heating Optimizer initialized")

    def _state_float(self, entity_id: str, default: float = 0.0) -> float:
        value = self.get_state(entity_id)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _state_str(self, entity_id: str, default: str = "") -> str:
        value = self.get_state(entity_id)
        if value is None:
            return default
        return str(value)

    def _read_inputs(self) -> OptimizerInputs:
        tempo_price_raw = self.get_state(self.entities["tempo_price"])
        tempo_price = None
        try:
            if tempo_price_raw not in (None, "", "unknown", "unavailable"):
                tempo_price = float(tempo_price_raw)
        except (TypeError, ValueError):
            tempo_price = None

        return OptimizerInputs(
            indoor_temp_c=self._state_float(self.entities["indoor_temp"], 19.0),
            setpoint_temp_c=self._state_float(self.entities["setpoint"], 20.0),
            tempo_color=self._state_str(self.entities["tempo_color"], "white"),
            tempo_period=self._state_str(self.entities["tempo_period"], "hp"),
            tempo_price_eur_kwh=tempo_price,
            pv_power_w=self._state_float(self.entities["pv_power"], 0.0),
            battery_soc_pct=self._state_float(self.entities["battery_soc"], 0.0),
            battery_power_w=self._state_float(self.entities["battery_power"], 0.0),
            surplus_solar_w=self._state_float(self.entities["surplus_solar"], 0.0),
            pellet_bag_price_eur=self._state_float(
                self.entities["pellet_bag_price"], 6.0
            ),
            pellet_bag_weight_kg=self._state_float(
                self.entities["pellet_bag_weight"], 15.0
            ),
        )

    def _set_climate_mode(self, entity_id: str, hvac_mode: str) -> None:
        if self.dry_run:
            self.log(f"[dry_run] climate/set_hvac_mode {entity_id} -> {hvac_mode}")
            return
        self.call_service(
            "climate/set_hvac_mode", entity_id=entity_id, hvac_mode=hvac_mode
        )

    def _apply_source(self, source: HeatingSource) -> None:
        source_to_entity = {
            HeatingSource.PELLET: self.entities["pellet_climate"],
            HeatingSource.AC: self.entities["ac_climate"],
            HeatingSource.RADIATOR: self.entities["radiator_climate"],
        }
        all_entities = list(source_to_entity.values())

        if source == HeatingSource.NONE:
            for entity in all_entities:
                self._set_climate_mode(entity, "off")
            return

        active_entity = source_to_entity[source]
        for entity in all_entities:
            mode = "heat" if entity == active_entity else "off"
            self._set_climate_mode(entity, mode)

    def _run_cycle(self, _kwargs) -> None:
        now = datetime.utcnow()
        inputs = self._read_inputs()
        decision = self.engine.decide(inputs, now=now)

        self.log(
            "decision="
            f"{decision.source.value} "
            f"reason={decision.reason} "
            f"elec={decision.electricity_cost_eur_kwh:.3f} "
            f"pellet={decision.pellet_cost_eur_kwh:.3f} "
            f"ac={decision.ac_cost_eur_kwh:.3f}"
        )

        self._apply_source(decision.source)
        self.engine.commit(decision.source, now=now)
