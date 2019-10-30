#!/usr/bin/python
#
#
import time
import Adafruit_DHT


def read():
    pin = 2
    sensor = Adafruit_DHT.DHT22

    h2, t2 = Adafruit_DHT.read_retry(sensor, pin)

    if h2 is None or t2 is None:
        h = 0
        t = 0
    else:
        h = h2
        t = t2

    return h, t


if __name__ == '__main__':
    while True:
        humidity, temperature = read()
        print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))

        # Wait half a second and repeat.
        time.sleep(0.5)
