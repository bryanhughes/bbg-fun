#! /usr/bin/env python
"""
This code will demonstrate how to use SMS to control a Beagle Bone Green using a Nimbelink Skywire modem.
"""
import sys
import gps_modem
import grove_dht
from datetime import datetime


def process_message(modem, from_number, message):
    lc_m = message.lower()
    print("Processing message: {}".format(lc_m))
    if lc_m.startswith('what time is it'):
        reply = datetime.now().strftime('Hi! According to my watch the time is %I:%M:%S %p UTC')
    elif lc_m.startswith('what is the temp'):
        try:
            hum, temp = grove_dht.read()
            reply = 'The temperature is {.2f} celsius with a humidity of {}%'.format(temp, hum)
        except Exception as e:
            print("Failed to read temperature: {}".format(e.message))
            reply = 'Sorry, I seem to be broken. :('
    else:
        print("Unknown message: {}".format(message))
        reply = 'Sorry. I am not that smart. Roses are red...'
    modem.write_message(from_number, reply)


def main():
    modem = gps_modem.GPSModem()
    modem.set_text_mode()

    while True:
        try:
            mt_message, sender = modem.pop_message()
            if mt_message is not None and sender is not None:
                process_message(modem, sender, mt_message)

        except KeyboardInterrupt:
            print("Caught keyboard interrupt. Bye!")
            if modem is not None:
                modem.reset_modem()
            sys.exit()


if __name__ == '__main__':
    main()
