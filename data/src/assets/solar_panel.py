"""Solar panel asset."""
from __future__ import annotations

from typing import Any

from .energy_asset import AssetError, EnergyAsset


class SolarPanel(EnergyAsset):
    """Solar array whose output depends on irradiance."""

    asset_type = "solar_panel"
    configurable_fields = ("name", "area_m2", "efficiency", "performance_ratio")

    def __init__(self, asset_id: str, name: str, area_m2: float,
                 efficiency: float = 0.2, performance_ratio: float = 0.8) -> None:
        super().__init__(asset_id, name)
        self._area_m2 = self._check_area(area_m2)
        self._efficiency = self._check_ratio(efficiency, "efficiency")
        self._performance_ratio = self._check_ratio(performance_ratio, "performance_ratio")
        self._last_generation_kwh = 0.0

    # ---- initialisation helpers (validation) ---------------------------------
    @staticmethod
    def _check_area(value: float) -> float:
        if value <= 0:
            raise AssetError("area_m2 must be positive")
        return float(value)

    @staticmethod
    def _check_ratio(value: float, field: str) -> float:
        if not 0 < value <= 1:
            raise AssetError(f"{field} must be in (0, 1]")
        return float(value)

    # ---- getters and setters -------------------------------------------------
    @property
    def area_m2(self) -> float:
        return self._area_m2

    @area_m2.setter
    def area_m2(self, value: float) -> None:
        self._area_m2 = self._check_area(value)

    @property
    def efficiency(self) -> float:
        return self._efficiency

    @efficiency.setter
    def efficiency(self, value: float) -> None:
        self._efficiency = self._check_ratio(value, "efficiency")

    @property
    def performance_ratio(self) -> float:
        return self._performance_ratio

    @performance_ratio.setter
    def performance_ratio(self, value: float) -> None:
        self._performance_ratio = self._check_ratio(value, "performance_ratio")

    @property
    def last_generation_kwh(self) -> float:
        """Result of the last calculation (derived value, so it has no setter)."""
        return self._last_generation_kwh

    # ---- behaviour -----------------------------------------------------------
    def reset(self) -> None:
        """Set-up method: forget the last calculated generation."""
        self._last_generation_kwh = 0.0

    def generation_kwh(self, irradiance_kwh_m2: float) -> float:
        """Energy generated for the given irradiance (kWh per m2 in the interval)."""
        if irradiance_kwh_m2 < 0:
            raise AssetError("irradiance must not be negative")
        self._last_generation_kwh = (self._area_m2 * irradiance_kwh_m2
                                     * self._efficiency * self._performance_ratio)
        return self._last_generation_kwh

    def specifications(self) -> dict[str, Any]:
        return {"area_m2": self._area_m2, "efficiency": self._efficiency,
                "performance_ratio": self._performance_ratio}

    def state(self) -> dict[str, Any]:
        return {"last_generation_kwh": self._last_generation_kwh}

    @classmethod
    def from_record(cls, asset_id, name, specs, state) -> "SolarPanel":
        panel = cls(asset_id, name, specs["area_m2"], specs.get("efficiency", 0.2),
                    specs.get("performance_ratio", 0.8))
        panel._last_generation_kwh = float(state.get("last_generation_kwh", 0.0))
        return panel
