"""Switch for Midea Lan."""

from typing import Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_SWITCHES, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICES, DOMAIN
from .midea_devices import MIDEA_DEVICES
from .midea_entity import MideaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches for device."""
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    extra_switches = config_entry.options.get(CONF_SWITCHES, [])
    switches = []
    for entity_key, config in cast(
        "dict",
        MIDEA_DEVICES[device.device_type]["entities"],
    ).items():
        if config["type"] == Platform.SWITCH and (
            config.get("default") or entity_key in extra_switches
        ):
            dev = MideaSwitch(device, entity_key)
            switches.append(dev)
    async_add_entities(switches)


class MideaSwitch(MideaEntity, ToggleEntity):
    """Represent a Midea switch."""

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        value = self._device.get_attribute(self._attribute_key)
        if "is_on_value" in self._config:
            return value == self._config["is_on_value"]
        return cast("bool", value)

    def turn_on(self, **kwargs: Any) -> None:  # noqa: ANN401, ARG002
        """Turn on switch."""
        if self._config.get("set_message") == "e1_start_pause":
            self._send_e1_work_status(0x03)
            return
        self._device.set_attribute(attr=self._entity_key, value=True)

    def turn_off(self, **kwargs: Any) -> None:  # noqa: ANN401, ARG002
        """Turn off switch."""
        if self._config.get("set_message") == "e1_start_pause":
            self._send_e1_work_status(0x01)
            return
        self._device.set_attribute(attr=self._entity_key, value=False)

    def _send_e1_work_status(self, work_status: int) -> None:
        """Set E1 dishwasher work status using midea-local's work message."""
        from midealocal.devices.e1.message import MessageWork

        mode_name = self._device.get_attribute("mode")
        modes: dict[int, str] = getattr(self._device, "_modes", {})
        mode = next((key for key, item in modes.items() if item == mode_name), 0)
        message = MessageWork(getattr(self._device, "_message_protocol_version"))
        message.work_status = work_status
        message.mode = mode
        self._device.build_send(message)
