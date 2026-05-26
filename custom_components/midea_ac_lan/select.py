"""Select for Midea Lan."""

from typing import Any, cast

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_SWITCHES, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from midealocal.device import MideaDevice

from .const import DEVICES, DOMAIN
from .midea_devices import MIDEA_DEVICES
from .midea_entity import MideaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up selects for device."""
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    extra_switches = config_entry.options.get(CONF_SWITCHES, [])
    selects = []
    for entity_key, config in cast(
        "dict",
        MIDEA_DEVICES[device.device_type]["entities"],
    ).items():
        if config["type"] == Platform.SELECT and (
            config.get("default") or entity_key in extra_switches
        ):
            dev = MideaSelect(device, entity_key)
            selects.append(dev)
    async_add_entities(selects)


class MideaSelect(MideaEntity, SelectEntity):
    """Represent a Midea select."""

    def __init__(self, device: MideaDevice, entity_key: str) -> None:
        """Midea select init."""
        super().__init__(device, entity_key)
        self._options_name = self._config.get("options")
        self._options_dict_name = self._config.get("options_dict")

    @property
    def options(self) -> list[str]:
        """Return entity options."""
        if self._options_dict_name:
            options = self._get_options_dict()
            if codes := self._config.get("options_codes"):
                return [options[code] for code in codes if code in options]
            return list(options.values())
        return cast("list", getattr(self._device, self._options_name))

    @property
    def current_option(self) -> str:
        """Return entity current option."""
        return cast("str", self._device.get_attribute(self._attribute_key))

    def select_option(self, option: str) -> None:
        """Select entity option."""
        if self._config.get("set_message") == "e1_work_mode":
            self._select_e1_work_mode(option)
            return
        self._device.set_attribute(self._entity_key, option)

    def _get_options_dict(self) -> dict[int, str]:
        """Return option dict from the backing midea-local device."""
        return cast("dict[int, str]", getattr(self._device, self._options_dict_name))

    def _select_e1_work_mode(self, option: str) -> None:
        """Set dishwasher work mode using midea-local's E1 work message."""
        mode = self._get_dict_key_by_value(self._get_options_dict(), option)
        if mode is None:
            raise ValueError(f"Unsupported dishwasher mode: {option}")

        from midealocal.devices.e1.message import MessageWork

        message = MessageWork(cast("Any", self._device)._message_protocol_version)
        message.mode = mode
        self._device.build_send(message)

    @staticmethod
    def _get_dict_key_by_value(source: dict[int, str], value: str) -> int | None:
        for key, item in source.items():
            if item == value:
                return key
        return None
