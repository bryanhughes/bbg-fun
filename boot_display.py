#!/usr/bin/env python
"""
boot_display.py - This script will display the IP address on the OLED Grove Display after the device has booted.
"""

import grove_oled
import gps_modem
import socket
import fcntl
import struct


def main():
    grove_oled.oled_init()
    grove_oled.oled_setNormalDisplay()
    grove_oled.oled_clearDisplay()
    grove_oled.oled_setTextXY(0,0)
    grove_oled.oled_putString("Hello...")

    hostname = socket.gethostname()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,  struct.pack('256s', 'eth0'[:15]))[20:24])

    print("Computer Name: " + hostname)
    print("Computer IP Address: " + ip)

    grove_oled.oled_setTextXY(0,0)
    grove_oled.oled_putString("IP:      ")
    grove_oled.oled_setTextXY(1,0)
    grove_oled.oled_putString(ip)

    # First we need initialize our modem so that we get our IMSI

    modem = gps_modem.GPSModem()
    imsi = modem.get_imsi()
    cell_ip = modem.get_ip()

    print("Setting display. IMSI: {} IP: {}".format(imsi, cell_ip))

    grove_oled.oled_setTextXY(3,0)
    grove_oled.oled_putString("IMSI:   ")
    grove_oled.oled_setTextXY(4,0)
    grove_oled.oled_putString(imsi)

    grove_oled.oled_setTextXY(6,0)
    grove_oled.oled_putString("Cell IP:")
    grove_oled.oled_setTextXY(7, 0)
    grove_oled.oled_putString(cell_ip)


if __name__ == "__main__":
    main()