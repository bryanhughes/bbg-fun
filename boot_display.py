#!/usr/bin/env python
"""
boot_display.py - This script will display the IP address on the OLED Grove Display after the device has booted.
"""

import grove_oled
import gps_modem


def main():
    grove_oled.oled_init()
    grove_oled.oled_setNormalDisplay()
    grove_oled.oled_clearDisplay()
    grove_oled.oled_setTextXY(0,0)
    grove_oled.oled_putString("Hello...")

    # First we need initialize our modem so that we get our IMSI

    modem = gps_modem.GPSModem()
    imsi = modem.get_imsi()
    ip = modem.get_ip()

    print("Setting display. IMSI: {} IP: {}".format(imsi, ip))

    grove_oled.oled_setTextXY(0,0)
    grove_oled.oled_putString("IMSI:   ")
    grove_oled.oled_setTextXY(1,0)
    grove_oled.oled_putString(imsi)

    grove_oled.oled_setTextXY(3,0)
    grove_oled.oled_putString("IP:")
    grove_oled.oled_setTextXY(4, 0)
    grove_oled.oled_putString(ip)


if __name__ == "__main__":
    main()