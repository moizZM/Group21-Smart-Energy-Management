"""Rebuild assets from stored database records."""
from __future__ import annotations

from typing import Any

from .battery import Battery
from .energy_asset import AssetError, EnergyAsset
from .smart_appliance import SmartAppliance
from .solar_panel import SolarPanel


ASSET_TYPES: dict[str, type[EnergyAsset]] = {
    cls.asset_type: cls for cls in (Battery, SolarPanel, SmartAppliance)
}


def asset_from_record(asset_type: str, asset_id: str, name: str,
                      specs: dict[str, Any], state: dict[str, Any]) -> EnergyAsset:
    """Factory used by the database layer."""
    if asset_type not in ASSET_TYPES:
        raise AssetError(f"Unknown asset type: {asset_type}")
    return ASSET_TYPES[asset_type].from_record(asset_id, name, specs, state)
