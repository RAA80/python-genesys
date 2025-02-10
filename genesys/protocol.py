#! /usr/bin/env python3

"""Реализация протокола управления программируемым источником питания GENESYS."""

from __future__ import annotations

import logging
import re
from time import sleep
from typing import TypedDict

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


class STATUS(TypedDict):
    MV: float
    PV: float
    MC: float
    PC: float
    SR: int
    FR: int


class GenesysError(Exception):
    pass


class Protocol:
    """Класс протокола работы с программируемым источником питания GENESYS."""

    @staticmethod
    def _make_packet(command: str, value: float | str | None = None) -> bytes:
        """Формирование пакета для записи."""

        msg = "" if value is None else f" {value}"
        return bytes(command + msg + "\r", encoding="ascii")

    def _bus_exchange(self, packet: bytes) -> bytes:
        """Обмен по интерфейсу."""

        raise NotImplementedError

    def _send(self, command: str, value: float | str | None = None) -> bytes:
        """Послать команду в устройство."""

        packet = self._make_packet(command.upper(), value)
        _logger.debug("Send frame = %r", packet)

        answer = self._bus_exchange(packet)
        _logger.debug("Recv frame = %r", answer)

        return answer

    def _set(self, command: str, value: float | None = None) -> bool:
        """Установить новое значение."""

        result = self._send(command=command, value=value)
        if result != b"OK\r":
            raise GenesysError(result)
        return True

    def _get_float(self, command: str) -> float:
        """Прочитать значение с плавающей точкой."""

        result = self._send(command=command)
        try:
            return float(result)
        except ValueError:
            raise GenesysError(result) from None

    def _get_int(self, command: str) -> int:
        """Прочитать целочисленное значение."""

        result = self._send(command=command)
        try:
            return int(result)
        except ValueError:
            raise GenesysError(result) from None

    def _get_string(self, command: str, pattern: set[bytes] | None = None) -> str:
        """Прочитать строковое значение."""

        result = self._send(command=command)
        if pattern and result not in pattern:
            raise GenesysError(result)
        return result.decode("ascii")

    # Initialization Control Commands

    def select_address(self, address: int) -> bool:
        """ADR is followed by address, which can be 0 to 30 and is used to access
        the power supply.
        """

        result = self._set("ADR", address)
        sleep(0.1)      # manual chapter 7.5.2
        return result

    def clear_status(self) -> bool:
        """Clear status. Sets FEVE and SEVE registers to zero."""

        return self._set("CLS")

    def reset(self) -> bool:
        """Reset command. Brings the power supply to a safe and known state."""

        return self._set("RST")

    def set_remote_mode(self, mode: int) -> bool:
        """Set the power supply to local or remote mode."""

        return self._set("RMT", mode)

    def get_remote_mode(self) -> str:
        """Return to the Remote mode setting."""

        return self._get_string("RMT?", {b"LOC\r", b"REM\r", b"LLO\r"})

    def get_multi_drop(self) -> int:
        """Return if Multi-drop option is installed. 1 indicates installed and 0
        indicates not installed.
        """

        return self._get_int("MDAV?")

    def get_ms_setting(self) -> int:
        """Return the Master/Slave setting. Master: n = 1, 2, 3, 4. Slave: n = 0."""

        return self._get_int("MS?")

    # ID Control Commands

    def get_model_identification(self) -> str:
        """Return the power supply model identification as an ASCII string."""

        return self._get_string("IDN?")

    def get_software_version(self) -> str:
        """Return the software version as an ASCII string."""

        return self._get_string("REV?")

    def get_serial_number(self) -> str:
        """Return the unit serial number. Up to 12 characters."""

        return self._get_string("SN?")

    def get_test_date(self) -> str:
        """Return date of last test. Date format: yyyy/mm/dd."""

        return self._get_string("DATE?")

    # Output Control Commands

    def set_voltage(self, value: float) -> bool:
        """Set the output voltage value in Volts."""

        return self._set("PV", value)

    def get_voltage(self) -> float:
        """Read the output voltage setting."""

        return self._get_float("PV?")

    def get_voltage_actual(self) -> float:
        """Read the actual output voltage."""

        return self._get_float("MV?")

    def set_current(self, value: float) -> bool:
        """Set the Output Current value in Amperes."""

        return self._set("PC", value)

    def get_current(self) -> float:
        """Read the Output Current setting."""

        return self._get_float("PC?")

    def get_current_actual(self) -> float:
        """Read the actual Output Current."""

        return self._get_float("MC?")

    def get_operation_mode(self) -> str:
        """Return the power supply operation mode."""

        return self._get_string("MODE?", {b"CV\r", b"CC\r", b"OFF\r"})

    def get_voltage_and_current(self) -> str:
        """Display Voltage and Current data. Data will be returned as a string of
        ASCII characters. A comma will separate the different fields.
        """

        return self._get_string("DVC?")

    def get_power_status(self) -> STATUS:
        """Read the complete power supply status."""

        result = self._get_string("STT?")
        status = re.sub(r"[a-z() ]*", "", result.lower()).split(",")

        return {"MV": float(status[0]),
                "PV": float(status[1]),
                "MC": float(status[2]),
                "PC": float(status[3]),
                "SR": int(status[4], 16),
                "FR": int(status[5], 16)}

    def set_filter(self, value: int) -> bool:
        """Set the low pass filter frequency of the A to D Converter for Voltage
        and Current Measurement where value = 18, 23 or 46 Hz (default is 18).
        """

        return self._set("FILTER", value)

    def get_filter(self) -> int:
        """Return the A to D Converter filter frequency: 18,23 or 46 Hz."""

        return self._get_int("FILTER?")

    def set_output(self, mode: int) -> bool:
        """Turn the output to ON or OFF."""

        return self._set("OUT", mode)

    def get_output(self) -> str:
        """Return the output On/Off status string."""

        return self._get_string("OUT?", {b"ON\r", b"OFF\r"})

    def set_foldback_protection(self, value: int) -> bool:
        """Set the Foldback protection to ON or OFF."""

        return self._set("FLD", value)

    def get_foldback_protection(self) -> str:
        """Return the Foldback protection status string."""

        return self._get_string("FLD?", {b"ON\r", b"OFF\r"})

    def set_foldback_delay(self, value: int) -> bool:
        """Add (value x 0.1) seconds to the Fold Back Delay. This delay is in
        addition to the standard 250 mSec delay. The range of nn is 0 to 255
        (0 to 25.5 Sec).
        """

        return self._set("FBD", value)

    def get_foldback_delay(self) -> int:
        """Supply returns the value of the added Fold Back Delay."""

        return self._get_int("FBD?")

    def reset_foldback_delay(self) -> bool:
        """Reset the added Fold Back Delay to zero. Restore the standard 250mSec
        delay.
        """

        return self._set("FBDRST")

    def set_over_voltage_protection_level(self, value: int) -> bool:
        """Set the OVP level."""

        return self._set("OVP", value)

    def get_over_voltage_protection_level(self) -> float:
        """Return the OVP setting."""

        return self._get_float("OVP?")

    def set_over_voltage_protection_maximum(self) -> bool:
        """Set OVP level to the maximum level."""

        return self._set("OVM")

    def set_under_voltage_limit(self, value: int) -> bool:
        """Set Under Voltage Limit."""

        return self._set("UVL", value)

    def get_under_voltage_limit(self) -> float:
        """Return the UVL setting."""

        return self._get_float("UVL?")

    def set_autorestart_mode(self, value: int) -> bool:
        """Set the Auto-restart mode to ON or OFF."""

        return self._set("AST", value)

    def get_autorestart_mode(self) -> str:
        """Return the string auto-restart mode status."""

        return self._get_string("AST?", {b"ON\r", b"OFF\r"})

    def save_settings(self) -> bool:
        """Save present settings. The settings are the same as power-down last
        setting. These settings are erased when the supply power is switched Off
        and the new “last settings” are saved.
        """

        return self._set("SAV")

    def recall_settings(self) -> bool:
        """Recall last settings."""

        return self._set("RCL")


__all__ = ["Protocol"]
