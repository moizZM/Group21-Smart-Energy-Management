"""Record types stored in the database (private attributes, validated properties)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

SEVERITIES = ("info", "warning", "critical")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _number(value: Any, field: str, minimum: float | None = None,
            optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    return float(value)


class _Record:
    """Shared behaviour: readable repr and comparison by value."""

    def _values(self) -> tuple:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and self._values() == other._values()  # type: ignore

    def __hash__(self) -> int:
        return hash((type(self).__name__, repr(self._values())))

    def __repr__(self) -> str:
        return f"{type(self).__name__}{self._values()!r}"


class EnergyReading(_Record):
    """One energy reading of one meter at one point in time."""

    def __init__(self, timestamp: datetime, asset_id: str, energy_kwh: float,
                 price: float | None = None, occupancy: int | None = None,
                 temperature: float | None = None, indoor_temperature: float | None = None,
                 hvac_status: int | None = None, solar_kwh: float | None = None) -> None:
        self.timestamp = timestamp
        self.asset_id = asset_id
        self.energy_kwh = energy_kwh
        self.price = price
        self.occupancy = occupancy
        self.temperature = temperature
        self.indoor_temperature = indoor_temperature
        self.hvac_status = hvac_status
        self.solar_kwh = solar_kwh

    def _values(self) -> tuple:
        return (self._timestamp, self._asset_id, self._energy_kwh, self._price, self._occupancy,
                self._temperature, self._indoor_temperature, self._hvac_status, self._solar_kwh)

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime) -> None:
        if not isinstance(value, datetime):
            raise ValueError("timestamp must be a datetime")
        self._timestamp = value

    @property
    def asset_id(self) -> str:
        return self._asset_id

    @asset_id.setter
    def asset_id(self, value: str) -> None:
        self._asset_id = _text(value, "asset_id")

    @property
    def energy_kwh(self) -> float:
        return self._energy_kwh

    @energy_kwh.setter
    def energy_kwh(self, value: float) -> None:
        self._energy_kwh = _number(value, "energy_kwh", minimum=0)

    @property
    def price(self) -> float | None:
        return self._price

    @price.setter
    def price(self, value: float | None) -> None:
        self._price = _number(value, "price", optional=True)

    @property
    def occupancy(self) -> int | None:
        return self._occupancy

    @occupancy.setter
    def occupancy(self, value: int | None) -> None:
        number = _number(value, "occupancy", minimum=0, optional=True)
        self._occupancy = None if number is None else int(number)

    @property
    def temperature(self) -> float | None:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float | None) -> None:
        self._temperature = _number(value, "temperature", optional=True)

    @property
    def indoor_temperature(self) -> float | None:
        return self._indoor_temperature

    @indoor_temperature.setter
    def indoor_temperature(self, value: float | None) -> None:
        self._indoor_temperature = _number(value, "indoor_temperature", optional=True)

    @property
    def hvac_status(self) -> int | None:
        return self._hvac_status

    @hvac_status.setter
    def hvac_status(self, value: int | None) -> None:
        if value is not None and value not in (0, 1):
            raise ValueError("hvac_status must be 0 (off), 1 (on) or None")
        self._hvac_status = None if value is None else int(value)

    @property
    def solar_kwh(self) -> float | None:
        return self._solar_kwh

    @solar_kwh.setter
    def solar_kwh(self, value: float | None) -> None:
        self._solar_kwh = _number(value, "solar_kwh", minimum=0, optional=True)


class SimulationResult(_Record):
    """Totals and parameters of one simulation run."""

    def __init__(self, run_name: str, totals: dict[str, float], cost: float,
                 parameters: dict[str, Any] | None = None,
                 details: dict[str, Any] | None = None) -> None:
        self.run_name = run_name
        self.totals = totals
        self.cost = cost
        self.parameters = parameters or {}
        self.details = details or {}

    def _values(self) -> tuple:
        return (self._run_name, self._totals, self._cost, self._parameters, self._details)

    @property
    def run_name(self) -> str:
        return self._run_name

    @run_name.setter
    def run_name(self, value: str) -> None:
        self._run_name = _text(value, "run_name")

    @property
    def totals(self) -> dict[str, float]:
        return dict(self._totals)

    @totals.setter
    def totals(self, value: dict[str, float]) -> None:
        if not isinstance(value, dict):
            raise ValueError("totals must be a dict")
        self._totals = dict(value)

    @property
    def cost(self) -> float:
        return self._cost

    @cost.setter
    def cost(self, value: float) -> None:
        self._cost = _number(value, "cost")

    @property
    def parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    @parameters.setter
    def parameters(self, value: dict[str, Any]) -> None:
        if not isinstance(value, dict):
            raise ValueError("parameters must be a dict")
        self._parameters = dict(value)

    @property
    def details(self) -> dict[str, Any]:
        return dict(self._details)

    @details.setter
    def details(self, value: dict[str, Any]) -> None:
        if not isinstance(value, dict):
            raise ValueError("details must be a dict")
        self._details = dict(value)


class Alert(_Record):
    """A warning raised for an asset."""

    def __init__(self, asset_id: str, severity: str, message: str,
                 timestamp: datetime | None = None, acknowledged: bool = False,
                 alert_id: int | None = None) -> None:
        self.asset_id = asset_id
        self.severity = severity
        self.message = message
        self.timestamp = timestamp or datetime.now()
        self.acknowledged = acknowledged
        self.alert_id = alert_id

    def _values(self) -> tuple:
        return (self._asset_id, self._severity, self._message, self._timestamp,
                self._acknowledged, self._alert_id)

    def acknowledge(self) -> None:
        self._acknowledged = True

    @property
    def asset_id(self) -> str:
        return self._asset_id

    @asset_id.setter
    def asset_id(self, value: str) -> None:
        self._asset_id = _text(value, "asset_id")

    @property
    def severity(self) -> str:
        return self._severity

    @severity.setter
    def severity(self, value: str) -> None:
        if value not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")
        self._severity = value

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, value: str) -> None:
        self._message = _text(value, "message")

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime) -> None:
        if not isinstance(value, datetime):
            raise ValueError("timestamp must be a datetime")
        self._timestamp = value

    @property
    def acknowledged(self) -> bool:
        return self._acknowledged

    @acknowledged.setter
    def acknowledged(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("acknowledged must be True or False")
        self._acknowledged = value

    @property
    def alert_id(self) -> int | None:
        return self._alert_id

    @alert_id.setter
    def alert_id(self, value: int | None) -> None:
        self._alert_id = None if value is None else int(value)
