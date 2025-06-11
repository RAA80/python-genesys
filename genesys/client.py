#! /usr/bin/env python3

"""Реализация клиентов для управления программируемым источником питания GENESYS."""

from __future__ import annotations

from dataclasses import dataclass
from socket import AF_INET, SOCK_STREAM, socket

from serial import Serial

from genesys.protocol import Protocol


@dataclass
class BaseClient(Protocol):
    """Базовый класс для работы с программируемым источником питания GENESYS."""

    address: str
    timeout: float = 1.0

    def __post_init__(self) -> None:
        """Инициализация параметров транспорта."""

        self.socket: Serial | socket

    def __del__(self) -> None:
        """Закрытие соединения с устройством при удалении объекта."""

        if self.socket:
            self.socket.close()

    def _bus_exchange(self, packet: bytes) -> bytes:
        """Обмен по интерфейсу."""

        raise NotImplementedError


@dataclass
class GenesysSerialClient(BaseClient):
    """Класс для работы с программируемым источником питания GENESYS через
    последовательный порт.
    """

    baudrate: int = 9600

    def __post_init__(self) -> None:
        """Инициализация параметров транспорта."""

        self.socket: Serial = Serial(port=self.address, baudrate=self.baudrate,
                                     timeout=self.timeout)

    def _bus_exchange(self, packet: bytes) -> bytes:
        """Обмен по интерфейсу."""

        self.socket.reset_input_buffer()
        self.socket.reset_output_buffer()

        self.socket.write(packet)
        return self.socket.read_until(b"\r")


@dataclass
class GenesysTcpClient(BaseClient):
    """Класс для работы с программируемым источником питания GENESYS через TCP."""

    def __post_init__(self) -> None:
        """Инициализация параметров транспорта."""

        ip, port = self.address.split(":")
        self.socket: socket = socket(AF_INET, SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.socket.connect((ip, int(port)))

    def _bus_exchange(self, packet: bytes) -> bytes:
        """Обмен по интерфейсу."""

        self.socket.sendall(packet)
        return self.socket.recv(128)


__all__ = ["GenesysSerialClient", "GenesysTcpClient"]
