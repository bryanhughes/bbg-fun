import smbus
import time


def read():
    bus = smbus.SMBus(2)
    bus.write_i2c_block_data(0x44, 0x2C, [0x06])
    time.sleep(0.5)
    data = bus.read_i2c_block_data(0x44, 0x00, 6)
    temp = data[0] * 256 + data[1]
    cTemp = -45 + (175 * temp / 65535.0)
    humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
    return humidity, cTemp


if __name__ == '__main__':
    while True:
        humidity, temperature = read()
        print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))

        # Wait half a second and repeat.
        time.sleep(0.5)
