"""Building: manages assets and steps the simulation."""
from __future__ import annotations

import logging
from typing import Iterable

from .battery import Battery
from .energy_asset import AssetError, EnergyAsset
from .smart_appliance import SmartAppliance
from .solar_panel import SolarPanel

logger = logging.getLogger(__name__)


class Building:
    """Manages a collection of assets and steps the simulation."""

    def __init__(self, name: str, location: str = "",
                 assets: Iterable[EnergyAsset] = ()) -> None:
        self._name = self._check_name(name)
        self._location = str(location).strip()
        self._assets: dict[str, EnergyAsset] = {}
        self.setup(assets)

    @staticmethod
    def _check_name(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AssetError("building name must be a non-empty string")
        return value.strip()

    # ---- getters and setters -------------------------------------------------
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = self._check_name(value)

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        self._location = str(value).strip()

    @property
    def assets(self) -> tuple[EnergyAsset, ...]:
        """Read-only view: assets are added with `register_asset`."""
        return tuple(self._assets.values())

    # ---- set-up and asset management -----------------------------------------
    def setup(self, assets: Iterable[EnergyAsset]) -> None:
        """Set-up method: register several assets at once (all or none)."""
        assets = list(assets)
        ids = [asset.asset_id for asset in assets]
        clash = set(ids) & set(self._assets) | {i for i in ids if ids.count(i) > 1}
        if clash:
            raise AssetError(f"Asset id already registered: {sorted(clash)}")
        for asset in assets:
            self._assets[asset.asset_id] = asset

    def register_asset(self, asset: EnergyAsset) -> None:
        if asset.asset_id in self._assets:
            raise AssetError(f"Asset id already registered: {asset.asset_id}")
        self._assets[asset.asset_id] = asset

    def get_asset(self, asset_id: str) -> EnergyAsset:
        try:
            return self._assets[asset_id]
        except KeyError as exc:
            raise AssetError(f"Unknown asset id: {asset_id}") from exc

    def remove_asset(self, asset_id: str) -> EnergyAsset:
        """Unregister and return an asset."""
        asset = self.get_asset(asset_id)
        del self._assets[asset_id]
        return asset

    # ---- simulation ------------------------------------------------------------
    def simulate_step(self, hours: float = 1.0,
                      irradiance_kwh_m2: float = 0.0) -> dict[str, float]:
        """Advance all assets one interval and balance supply and demand."""
        solar = sum(a.generation_kwh(irradiance_kwh_m2)
                    for a in self._assets.values() if isinstance(a, SolarPanel))
        demand = sum(a.run(hours)
                     for a in self._assets.values() if isinstance(a, SmartAppliance))
        batteries = [a for a in self._assets.values() if isinstance(a, Battery)]
        surplus, deficit = max(solar - demand, 0.0), max(demand - solar, 0.0)
        charged = discharged = 0.0
        for bat in batteries:
            charged += bat.charge(surplus - charged)
            discharged += bat.discharge(deficit - discharged)
        result = {
            "solar_kwh": solar, "appliance_kwh": demand,
            "battery_charged_kwh": charged, "battery_discharged_kwh": discharged,
            "grid_import_kwh": deficit - discharged,
            "grid_export_kwh": surplus - charged,
        }
        logger.debug("Simulation step: %s", result)
        return result
