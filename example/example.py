#! /usr/bin/env python3

"""Пример использования библиотеки."""

import logging

from genesys.client import GenesysSerialClient, GenesysTcpClient

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    client = GenesysSerialClient(address="COM5", baudrate=9600)
    # client = GenesysTcpClient(address="127.0.0.1:5000")
    print(client)

    print(client.select_address(address=6))

    print(client.set_voltage(value=10.0))
    print(client.set_current(value=3.0))
    print(client.set_remote_mode(mode=1))
    print(client.set_output(mode=1))

    print(client.get_voltage())
    print(client.get_current())
    print(client.get_remote_mode())
    print(client.get_output())
