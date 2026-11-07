"""Battery energy storage asset."""
from __future__ import annotations

from typing import Any

from .energy_asset import AssetError, EnergyAsset


class Battery(EnergyAsset):
    """Battery energy storage with a state of charge."""

    asset_type = "battery"
    configurable_fields = ("name", "capacity_kwh", "efficiency", "stored_kwh")

    def __init__(self, asset_id: str, name: str, capacity_kwh: float,
                 efficiency: float = 0.95, stored_kwh: float = 0.0) -> None:
        super().__init__(asset_id, name)
        self._capacity_kwh = self._check_capacity(capacity_kwh)
        self._efficiency = self._check_efficiency(efficiency)
        self._stored_kwh = self._check_stored(stored_kwh, self._capacity_kwh)

    # ---- initialisation helpers (validation) ---------------------------------
    @staticmethod
    def _check_capacity(value: float) -> float:
        if value <= 0:
            raise AssetError("capacity_kwh must be positive")
        return float(value)

    @staticmethod
    def _check_efficiency(value: float) -> float:
        if not 0 < value <= 1:
            raise AssetError("efficiency must be in (0, 1]")
        return float(value)

    @staticmethod
    def _check_stored(value: float, capacity: float) -> float:
        if not 0 <= value <= capacity:
            raise AssetError("stored_kwh must be between 0 and capacity_kwh")
        return float(value)

    # ---- getters and setters -------------------------------------------------
    @property
    def capacity_kwh(self) -> float:
        return self._capacity_kwh

    @capacity_kwh.setter
    def capacity_kwh(self, value: float) -> None:
        new = self._check_capacity(value)
        if new < self._stored_kwh:
            raise AssetError("capacity_kwh cannot be below the energy currently stored")
        self._capacity_kwh = new

    @property
    def efficiency(self) -> float:
        return self._efficiency

    @efficiency.setter
    def efficiency(self, value: float) -> None:
        self._efficiency = self._check_efficiency(value)

    @property
    def stored_kwh(self) -> float:
        return self._stored_kwh

    @stored_kwh.setter
    def stored_kwh(self, value: float) -> None:
        self._stored_kwh = self._check_stored(value, self._capacity_kwh)

    @property
    def state_of_charge_percent(self) -> float:
        return 100.0 * self._stored_kwh / self._capacity_kwh

    @state_of_charge_percent.setter
    def state_of_charge_percent(self, percent: float) -> None:
        if not 0 <= percent <= 100:
            raise AssetError("state of charge must be between 0 and 100 percent")
        self._stored_kwh = self._capacity_kwh * percent / 100.0

    # ---- behaviour -----------------------------------------------------------
    def reset(self, stored_kwh: float = 0.0) -> None:
        """Set-up method: bring the battery back to a known state of charge."""
        self.stored_kwh = stored_kwh

    def charge(self, kwh: float) -> float:
        """Offer `kwh` to the battery; return the energy actually taken."""
        if kwh < 0:
            raise AssetError("kwh must not be negative")
        free = self._capacity_kwh - self._stored_kwh
        taken = min(kwh, free / self._efficiency)
        self._stored_kwh += taken * self._efficiency
        return taken

    def discharge(self, kwh: float) -> float:
        """Request `kwh` from the battery; return the energy actually delivered."""
        if kwh < 0:
            raise AssetError("kwh must not be negative")
        delivered = min(kwh, self._stored_kwh)
        self._stored_kwh -= delivered
        return delivered

    def specifications(self) -> dict[str, Any]:
        return {"capacity_kwh": self._capacity_kwh, "efficiency": self._efficiency}

    def state(self) -> dict[str, Any]:
        return {"stored_kwh": self._stored_kwh,
                "soc_percent": round(self.state_of_charge_percent, 2)}

    @classmethod
    def from_record(cls, asset_id, name, specs, state) -> "Battery":
        return cls(asset_id, name, specs["capacity_kwh"], specs.get("efficiency", 0.95),
                   state.get("stored_kwh", 0.0))
