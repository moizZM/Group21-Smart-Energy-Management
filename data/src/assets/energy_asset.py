"""Abstract base class for all energy assets."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AssetError(ValueError):
    """Raised for invalid asset parameters or operations."""


class EnergyAsset(ABC):
    """Abstract energy asset with an identity (id, name) and a state.

    Attributes are private; they are read and changed only through properties, and every
    setter validates its input. The id identifies the asset in the database, so it is
    read-only after construction.
    """

    asset_type: str = "asset"
    #: names of the properties that `configure` is allowed to change
    configurable_fields: tuple[str, ...] = ("name",)

    def __init__(self, asset_id: str, name: str) -> None:
        self._asset_id = self._check_text(asset_id, "asset_id")
        self._name = self._check_text(name, "name")

    @staticmethod
    def _check_text(value: Any, field: str) -> str:
        """Initialisation helper: return a stripped, non-empty string or raise."""
        if not isinstance(value, str) or not value.strip():
            raise AssetError(f"{field} must be a non-empty string")
        return value.strip()

    # ---- getters and setters -------------------------------------------------
    @property
    def asset_id(self) -> str:
        return self._asset_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = self._check_text(value, "name")

    # ---- configuration -------------------------------------------------------
    def configure(self, **settings: Any) -> None:
        """Apply several settings at once; if one is invalid nothing is changed."""
        unknown = [key for key in settings if key not in self.configurable_fields]
        if unknown:
            raise AssetError(f"Unknown or read-only setting(s): {unknown}")
        snapshot = dict(self.__dict__)
        try:
            for key, value in settings.items():
                setattr(self, key, value)
        except AssetError:
            self.__dict__.clear()
            self.__dict__.update(snapshot)
            raise

    @abstractmethod
    def specifications(self) -> dict[str, Any]:
        """Fixed technical data (capacity, area, rated power ...)."""

    @abstractmethod
    def state(self) -> dict[str, Any]:
        """Current changing state of the asset."""

    @classmethod
    @abstractmethod
    def from_record(cls, asset_id: str, name: str,
                    specs: dict[str, Any], state: dict[str, Any]) -> "EnergyAsset":
        """Rebuild an asset from stored specifications and state."""
