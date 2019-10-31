# Beagle Bone Green + Grove

This is a collection of Python code, tricks, and instructions that I have collected that works with the Beagle Bone Green and
Beagle Bone Green Wireless.

#### WARNING
```
ALWAYS SHUTDOWN THE DEVICE EITHER BY PRESSING THE POWER BUTTON (see documentation on the Beaglebone) OR 
BY ISSUING THE SHUTDOWN COMMAND. 

UNPLUGGING THE POWER CAN CAUSE DAMAGE.
```    

### Configuring The Wifi
There are [instructions](https://beagleboard.org/green-wireless) for configuring the wifi on the Beaglebone by connecting 
to the SeeedStudio BeagleBone Green Wireless AP and then selecting your SSID and entering your passphrase.

This does not always work. If it doesnt, the you will need to configure it manually by logging onto the device using either
screen or ssh, and type the following

	$ connmanctl (invoke utility)
	connmanctl> tether wifi off (disable tethering)
	connmanctl> enable wifi (enable wifi radio)
	connmanctl> scan wifi (scan for AP, might take a few seconds)
	connmanctl> services (display detected AP)
	connmanctl> agent on (enable connection agent)
	connmanctl> connect wifi_*_managed_psk (connect to selected AP, might take some time, will prompt for password)
	connmanctl> quit
	
Test your connection...

    $ ping yahoo.com	

### Update The Software
You may need to ensure your UART-4 serial port is enabled. If is is not, then you will need to edit
the `/boot/uEnv.txt`. Be very careful modifying this file.

    $ sudo vi /boot/uEnv.txt 

Find the section for v4.1.x and uncomment the `cape_enable` and then add `BB_UART4`

```
##Example v4.1.x
#cape_disable=bone_capemgr.disable_partno=
cape_enable=bone_capemgr.enable_partno=BB-UART4
```

After reboot, the device is present in the device list. UART-4 is linked as ttyO4:

```
$ ls -l /dev/ttyO*
lrwxrwxrwx 1 root root 5 Nov 26 23:00 /dev/ttyO0 -> ttyS0
lrwxrwxrwx 1 root root 5 Nov 26 23:00 /dev/ttyO3 -> ttyS3
lrwxrwxrwx 1 root root 5 Nov 26 23:00 /dev/ttyO4 -> ttyS4
```

Next, update your software:

    $ sudo apt-get update
    $ sudo apt-get upgrade

Now update your kernel (you should be running Debian by default) and reboot:


    $ cd /opt/scripts/tools/
    $ git pull
    $ sudo ./update_kernel.sh
    $ sudo reboot

Your SSH connection should drop, but you can pull it back up as soon as the Beaglebone finishes rebooting.

### Installing The Python Components

First, make sure your Python is up to date. This is all done on the Beaglebone. 

    $ sudo apt-get install build-essential python-dev python-smbus python-setuptools python-pip -y

Finally, you will need to install the [Adafruit Python ADXL345](https://github.com/adafruit/Adafruit_Python_ADXL345) libraries. You
can either do this manually, or you can install from pip with:

    $ sudo pip install adafruit-adxl345 
    
### Developing a Cellular Prototype
The Beagle Bone Green and Raspberry Pi are great Single Board Computers (SBC) for developing and prototyping IoT devices that
need some form of cellular connection for data transmission. While everyone is rushing to NB-IoT and LTE-M CatM1 (and someday CatM0)
because of low power requirements, today there is single option that can work for multi-years in the field under battery 
power: SMS messaging in PDU mode.

I have developed prototypes working with variety of ways and with a variety of MNO and MVNO providers. I have tested 
this using SIMS from [Aeris Neo](https://www.aeris.com/neo/), [Twilio](https://www.twilio.com/wireless)^, 
and [Verizon](https://nimbelink.com/products/nl-sim-ver-m1/)

#### Aeris
Aeris is very straight forward. You can purchase your SIMs at their [Neo](https://www.aeris.com/neo/) portal. After
your SIMs arrive, you will then be given access to create an account and start using their APIs. In a nutshell, Aeris 
offers a very clean long polling service that your server calls to poll for any data. Aeris is a great choice for solutions
that are based solely on SMS messages as the transport for device telemetry. SMS is a much overlooked solution for sending
device telemetry where the device needs to operate on a cellular network, around the world, and needs to operate on battery
power.

#### Twilio
[more to come]

#### Verizon
Unlike Aeris and Twilio which are MVNO's that are reselling network access, Verizon gives your device 
direct access which means that Mobile Originated (MO) SMS messages can be sent directly from your IoT device
to any valid phone number in the world. You can also receive Mobile Terminated (MT) SMS messages, along with creating a
PPP connection for streaming data.
    
    
## gps_modem.py + serial_mutex.py
This code demonstrate how to use the Nimbelink [Skywire Global LTE-M](https://nimbelink.com/products/4g-lte-m-global-quectel/) modem 
and the Nimbelink [Skywire BB Cape Lite Developer Kit](https://nimbelink.com/products/skywire-beaglebone-cape-lite/). 
You can use this in a variety of ways and with a variety of MNO and MVNO's. I have tested this using SIMS from
[Aeris Neo](https://www.aeris.com/neo/), [Twilio](https://www.twilio.com/wireless)^, and [Verizon](https://nimbelink.com/products/nl-sim-ver-m1/)

Please note that Aeris and Twilio are MVNO's while Verizon is a MNO. If you plan on using Aeris or Twilio, you will need
code to integrate with their back-end services to pull your data. 

^ Not yet tested end-to-end. Successfully registered on network.

#### Does it work?
```
$ sudo python grove_dht.py
```
You should see the following output:

```bash
$ sudo python grove_dht.py
Temp=25.3*  Humidity=24.2%
Temp=24.6*  Humidity=25.1%
Temp=24.6*  Humidity=25.1%
Temp=24.6*  Humidity=25.1%
<snip>
```

## grove_accel.py
You will need to install the [Adafruit Python ADXL345](https://github.com/adafruit/Adafruit_Python_ADXL345) libraries. You
can either do this manually, or you can install from pip with:

    $ sudo pip install adafruit-adxl345   
    
#### Does it work?
```
$ sudo python grove_accel.py
```
You should see the following output:

```bash
$ sudo python grove_dht.py
Temp=23.7*  Humidity=2.3%
Temp=23.7*  Humidity=2.6%
Temp=23.7*  Humidity=2.6%
Temp=23.7*  Humidity=2.6%
<snip>
```
         

## grove_dht.py
To use the DHT sensor, you will need to download the [Adafruit Python DHT Sensor Library](https://github.com/adafruit/Adafruit_Python_DHT.git)

    $ cd ~
    $ git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    $ cd Adafruit_Python_DHT
    $ sudo python setup.py install 
    
If there any issues, or more detail, read the README.md.

#### Does it work?
```
$ sudo python grove_dht.py
```
You should see the following output:

```bash
$ sudo python grove_dht.py
Temp=25.3*  Humidity=24.2%
Temp=24.6*  Humidity=25.1%
Temp=24.6*  Humidity=25.1%
Temp=24.6*  Humidity=25.1%
<snip>
```


## grove_sht31.py
[add here]

## grove_oled.py
The current Python code is a few years old but still works. Unfortunately, one of the Adafruit libraries is being
deprecated. At the time of this post (10/30/2019) the code works. First, connect the OLED Display to the IC2 Grove Connector 
on the Beaglebone Green development board. If the connector is occupied by another sensor, then you should consider
getting the [Grove Base Cape](https://www.seeedstudio.com/Grove-Base-Cape-for-Beaglebone-v2-0-p-2644.html) for supporting
more devices.

Once you have your Grove OLED installed in the IC2 connector, you will need to install the following packages:

#### Install the adafruit_gpio
```
$ sudo apt-get update
$ sudo apt-get install build-essential python-pip python-dev python-smbus git
$ sudo pip install Adafruit-GPIO
```

#### Install adafruit_bbio
```
sudo apt-get install build-essential python-dev python-pip -y
sudo pip install Adafruit_BBIO
```

#### Does it work?
```
$ sudo python grove_oled.py
```
You should see 'Hello' on the display

## grove_led.py
[add here]

# Other Components
Depending on the board that you are prototyping with, they will be configured with one or more USB slots. If you decide 
to use one for a USB Bluetooth Dongle, be prepared for a challenge. I am using a 
(Plugable Dongle)[https://www.amazon.com/gp/product/B009ZIILLI]  that I purchased on Amazon. It uses the a Broadcom chipset
and not surprisingly is not fully supported on the Beagle Bone Green. 

```bash
dmesg | grep -i blue
[   53.576284] Bluetooth: Core ver 2.21
[   53.576492] Bluetooth: HCI device and connection manager initialized
[   53.576522] Bluetooth: HCI socket layer initialized
[   53.576538] Bluetooth: L2CAP socket layer initialized
[   53.576595] Bluetooth: SCO socket layer initialized
[   53.824668] Bluetooth: hci0: BCM: chip id 63
[   53.841367] Bluetooth: hci0: BCM20702A
[   53.842346] Bluetooth: hci0: BCM20702A1 (001.002.014) build 0000
[   53.847327] bluetooth hci0: Direct firmware load for brcm/BCM20702A1-0a5c-21e8.hcd failed with error -2
[   53.847368] Bluetooth: hci0: BCM: Patch brcm/BCM20702A1-0a5c-21e8.hcd not found

```

Then you will need to follow the instructions here:

https://plugable.com/2014/06/23/plugable-usb-bluetooth-adapter-solving-hfphsp-profile-issues-on-linux/

```bash
dmesg | grep -i blue
[   51.998663] Bluetooth: Core ver 2.21
[   52.019350] Bluetooth: HCI device and connection manager initialized
[   52.019391] Bluetooth: HCI socket layer initialized
[   52.019407] Bluetooth: L2CAP socket layer initialized
[   52.019525] Bluetooth: SCO socket layer initialized
[   52.235321] Bluetooth: hci0: BCM: chip id 63
[   52.251372] Bluetooth: hci0: BCM20702A
[   52.252353] Bluetooth: hci0: BCM20702A1 (001.002.014) build 0000
[   52.975322] Bluetooth: hci0: BCM20702A1 (001.002.014) build 1338
[   52.991368] Bluetooth: hci0: Broadcom Bluetooth Device
[   59.944556] Bluetooth: BNEP (Ethernet Emulation) ver 1.3
[   59.944584] Bluetooth: BNEP filters: protocol multicast
[   59.944614] Bluetooth: BNEP socket layer initialized
[   60.306830] Bluetooth: RFCOMM TTY layer initialized
[   60.306894] Bluetooth: RFCOMM socket layer initialized
[   60.308989] Bluetooth: RFCOMM ver 1.11
```

Everything is reporting no errors. Unfortunately at this point I was still not getting any audio to play. After spending
a day, I realized that while I was fumbling around, that I had installed both pulseaudio and bluealsa, but not really. 

The next step I took was to build from source [bluealsa](https://github.com/Arkq/bluez-alsa). Be patient as none of the
developer versions of the dependencies were on my device, so each time through the config I had to install the 
missing developer version of the libraries. For me it was:

```
$ sudo apt-get install libasound2-dev libbluetooth-dev libsbc-dev libfdk-aac-dev
```

After making and installing the bluealsa, unfortunately it still did not work. A quick search and
I found this [github issue](https://github.com/Arkq/bluez-alsa/issues/72) that explained that pulseaudio and
bluealsa do not work together, so I removed pulseaudio

```bash
$ sudo  apt-get --purge remove pulseaudio
```

Then did a shutdown (power off) and then restarted and it worked. Make sure you follow the configuration and setup 
instructions.