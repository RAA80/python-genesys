#! /usr/bin/env python3

"""Реализация класса клиента для управления программируемым источником
питания GENESYS.
"""

from __future__ import annotations

import select
import socket
from time import time

from serial import Serial

from .protocol import Protocol


class GenesysSerialClient(Protocol):
    """Класс для работы с программируемым источником питания GENESYS через
    последовательный порт.
    """

    def __init__(self, port: str, baudrate: int, timeout: float = 1.0) -> None:
        """Инициализация класса клиента с указанными параметрами."""

        self.socket = Serial(port=port, baudrate=baudrate, timeout=timeout)

        self.port = port
        self.baudrate = baudrate

    def __del__(self) -> None:
        """Закрытие соединения с устройством при удалении объекта."""

        if self.socket.is_open:
            self.socket.close()

    def __repr__(self) -> str:
        """Строковое представление объекта."""

        return f"{type(self).__name__}(port={self.port!r}, baudrate={self.baudrate})"

    def _bus_exchange(self, packet: bytes) -> bytes:
        """Обмен по интерфейсу."""

        self.socket.reset_input_buffer()
        self.socket.reset_output_buffer()

        self.socket.write(packet)
        return self.socket.read_until(b"\r")


class GenesysTcpClient(Protocol):
    """Класс для работы с программируемым источником питания GENESYS через TCP."""

    def __init__(self, port: str, timeout: float = 1.0) -> None:
        """Инициализация класса клиента с указанными параметрами."""

        ip, tcp_port = port.split(":")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)
        self.socket.connect((ip, int(tcp_port)))

        self.port = port
        self.timeout = timeout

    def __del__(self) -> None:
        """Закрытие соединения с устройством при удалении объекта."""

        if self.socket:
            self.socket.close()

    def __repr__(self) -> str:
        """Строковое представление объекта."""

        return f"{type(self).__name__}(port={self.port!r}, timeout={self.timeout})"

    def _tcp_read(self, timeout: float, stop_byte: bytes | None = None) -> bytes:
        """Чтение ответных данных."""

        max_t = time() + timeout
        ret = b""
        while True:
            to_wait = max(0.0, max_t - time())
            r, _, _ = select.select([self.socket], [], [], to_wait)
            if self.socket not in r:
                break
            chunk = self.socket.recv(1)
            ret += chunk
            if len(chunk) == 0 or chunk == stop_byte:
                break
        return ret

    def _bus_exchange(self, packet: bytes) -> bytes:
        """Обмен по интерфейсу."""

        self._tcp_read(0.0)  # drain input buffer
        self.socket.send(packet)
        return self._tcp_read(self.timeout, b"\r")


__all__ = ["GenesysSerialClient", "GenesysTcpClient"]
