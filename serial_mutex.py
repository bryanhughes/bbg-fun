#!/usr/bin/env python
"""
serial_mutex.py - A class to provide a mutex on key serial operations to the modem
"""

import serial
import logging
import time
from threading import Lock


class SerialMutex(object):
    def __init__(self):
        fmt = '%(asctime)-15s %(message)s'
        logging.basicConfig(format=fmt, level=logging.INFO)
        self.logger = logging.getLogger('serial_mutex')
        self.ser = serial.Serial('/dev/ttyO4', 115200, timeout=5)
        self.lock = Lock()

    def write_message(self, recipient, binary_content):
        with self.lock:
            octets, pdu = self.make_pdu(recipient, binary_content)
            self.logger.info("[serial_mutex] octets = %d, pdu = %s", octets, pdu)

            self.ser.write('AT+CMGS=' + str(octets) + '\r')
            time.sleep(.500)
            self.ser.write(pdu + "\r")
            time.sleep(.500)
            rx_buffer = self.write_(chr(26), 5)
            if rx_buffer.find('OK') == -1:
                self.logger.error("[serial_mutex] Failed to send pdu sms message: [%s]", rx_buffer)
                raise IOError("Failed to send sms message")

    def make_pdu(self, recipient, message):
        # http://www.gsmfavorites.com/documents/sms/pdutext/

        # First octet, Length of SMSC information. Here the length is 0, which means that the SMSC stored in the phone
        # should be used. Note: This octet is optional. On some  phones this octet should be omitted! (Using the SMSC
        # stored in phone is thus implicit)

        # Second octet - the SMS-SUBMIT message - '11'

        # Third octet - TP-Message-Reference. The "00" value here lets the phone set the message
        # reference number itself.

        # Forth octect - Address-Length. Length of phone number

        # Fifth octect - Type-of-Address. (91 indicates international format of the phone number).

        pdu = ['00', '11', '00', '0A', '91']

        # Address needs to be swapped 4155157916 to 14 55 51 97 61

        recipient = self.encode_address(recipient, [])
        self.logger.info("recipient = %s", recipient)
        pdu.append(recipient)

        # TP-PID. Protocol identifier

        pdu.append('00')

        # TP-DCS. 8 bit data indicates the UD is coded in 8-bit format and result a maximum of characters of
        # 140 in a message. We use the value 04 because its mask represents an 8-bit message
        #
        # see also http://read.pudn.com/downloads150/sourcecode/embed/646395/Short%20Message%20in%20PDU%20Encoding.pdf

        pdu.append('04')

        # TP-Validity-Period. "C2" means 4 weeks:

        pdu.append('C2')

        # TP-User-Data-Length. Length of message. The TP-DCS field indicated 7-bit  data, so the length here is the
        # number of septets (10). If the TP-DCS field were set to 8-bit data or Unicode, the length would be the
        # number of octets.

        mlen = len(message)
        pdu.append('%02X' % mlen)

        self.logger.info(">>>> mlen = %d / %s", mlen, '%02X' % mlen)

        # TP-User-Data.
        [pdu.append('%02X' % ord(y)) for y in message]

        self.logger.info(">>>> %s", ['%02X ' % ord(y) for y in message])
        self.logger.info(">>>> %s", pdu)

        pdu_str = ''.join(pdu)
        octect = (len(pdu_str) - 2) / 2

        return octect, ''.join(pdu)

    def encode_address(self, addr, accum):
        if len(addr) <= 0:
            return ''.join(accum)
        (a, b), rest = addr[:2], addr[2:]
        accum.append(b)
        accum.append(a)
        return self.encode_address(rest, accum)

    def write(self, command):
        with self.lock:
            return self.write_(command, 1)

    def write_wait(self, command, sleep_time):
        with self.lock:
            return self.write_(command, sleep_time)

    def write_(self, command, sleep_time):
        self.ser.write(command)
        self.ser.flushOutput()
        time.sleep(sleep_time)
        rx_buffer = ''
        stime = time.time()
        # Wait for our OK in our response buffer
        while True:
            rx_buffer += self.ser.read(1)
            if time.time() - stime > 60:
                self.logger.warn("[serial_mutex] Timed out - no response from modem => %s", command)
                break
            elif self.ser.inWaiting() > 0:
                while self.ser.inWaiting():
                    rx_buffer += (self.ser.read(self.ser.inWaiting()))
                if rx_buffer.find('OK') != -1 or rx_buffer.find('ERROR') != -1:
                    # self.logger.info("BREAK - %s", rx_buffer)
                    break

        self.logger.info("[serial_mutex] rx_buffer = %s", [rx_buffer])
        self.ser.flush()
        return rx_buffer

    def close(self):
        with self.lock:
            self.ser.close()

    def reset_modem(self):
        with self.lock:
            self.ser.write(chr(26))
            self.ser.write('AT+CRES')
