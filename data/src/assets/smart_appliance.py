"""Smart appliance asset."""
from __future__ import annotations

from typing import Any

from .energy_asset import AssetError, EnergyAsset


class SmartAppliance(EnergyAsset):
    """Appliance that can be switched on/off and tracks consumption."""

    asset_type = "smart_appliance"
    configurable_fields = ("name", "rated_power_kw", "status", "total_kwh")

    def __init__(self, asset_id: str, name: str, rated_power_kw: float,
                 status: bool = False, total_kwh: float = 0.0) -> None:
        super().__init__(asset_id, name)
        self._rated_power_kw = self._check_power(rated_power_kw)
        self._status = bool(status)
        self._total_kwh = self._check_total(total_kwh)

    # ---- initialisation helpers (validation) ---------------------------------
    @staticmethod
    def _check_power(value: float) -> float:
        if value <= 0:
            raise AssetError("rated_power_kw must be positive")
        return float(value)

    @staticmethod
    def _check_total(value: float) -> float:
        if value < 0:
            raise AssetError("total_kwh must not be negative")
        return float(value)

    # ---- getters and setters -------------------------------------------------
    @property
    def rated_power_kw(self) -> float:
        return self._rated_power_kw

    @rated_power_kw.setter
    def rated_power_kw(self, value: float) -> None:
        self._rated_power_kw = self._check_power(value)

    @property
    def status(self) -> bool:
        return self._status

    @status.setter
    def status(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise AssetError("status must be True (on) or False (off)")
        self._status = value

    @property
    def total_kwh(self) -> float:
        return self._total_kwh

    @total_kwh.setter
    def total_kwh(self, value: float) -> None:
        self._total_kwh = self._check_total(value)

    # ---- behaviour -----------------------------------------------------------
    def turn_on(self) -> None:
        self._status = True

    def turn_off(self) -> None:
        self._status = False

    def reset(self) -> None:
        """Set-up method: switch off and clear the consumption counter."""
        self._status = False
        self._total_kwh = 0.0

    def run(self, hours: float) -> float:
        """Run for `hours`; return energy used (0 if switched off)."""
        if hours < 0:
            raise AssetError("hours must not be negative")
        if not self._status:
            return 0.0
        used = self._rated_power_kw * hours
        self._total_kwh += used
        return used

    def specifications(self) -> dict[str, Any]:
        return {"rated_power_kw": self._rated_power_kw}

    def state(self) -> dict[str, Any]:
        return {"status": self._status, "total_kwh": self._total_kwh}

    @classmethod
    def from_record(cls, asset_id, name, specs, state) -> "SmartAppliance":
        return cls(asset_id, name, specs["rated_power_kw"],
                   state.get("status", False), state.get("total_kwh", 0.0))
