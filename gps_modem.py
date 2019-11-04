#!/usr/bin/env python
"""
gps_modem.py - used to work with the modem.
"""
import logging
import time
import serial_mutex
import re
import sys


def to_bytes(s):
    if sys.version_info >= (3,):
        return bytes(s)
    return ''.join(map(unichr, s))


class GPSModem:
    def __init__(self):
        self.sms_mode = 1
        fmt = '%(asctime)-15s %(message)s'
        logging.basicConfig(format=fmt, level=logging.INFO)
        self.logger = logging.getLogger('gps_modem')
        self.ser = serial_mutex.SerialMutex()
        self.is_ok()
        self.logger.info("[gps_modem] Modem is ready...testing states")
        self.set_verbose_error()
        self.test_cfun()
        self.test_qcsq()
        self.test_cereg()
        self.test_qiact(0)
        self.test_sms_service()
        self.test_gps()
        self.set_text_mode()
        self.logger.info("[gps_modem] ready...")

    def set_verbose_error(self):
        self.logger.info("[gps_modem] Enabling detailed error messages...")
        out = self.ser.write('AT+CMEE=2\r')
        if out.find('OK') == -1:
            self.logger.error("[gps_modem] Failed to enable detailed error messages (AT+CMEE=2). out=%s", out)
            raise IOError("Failed to enable detailed error messages")

    def set_pdu_mode(self):
        self.sms_mode = 0
        self.logger.info("[gps_modem] Setting SMS message to PDU mode...")
        out = self.ser.write('AT+CMGF=0\r')
        if out.find('OK') == -1:
            self.logger.error("[gps_modem] Failed to set PDU mode (AT+CMGF=0). out=%s", out)
            raise IOError("Failed to set PDU mode")

    def set_text_mode(self):
        self.sms_mode = 1
        self.logger.info("[gps_modem] Setting SMS message to Text mode...")
        out = self.ser.write('AT+CMGF=1\r')
        if out.find('OK') == -1:
            self.logger.error("[gps_modem] Failed to set Text mode (AT+CMGF=1). out=%s", out)
            raise IOError("Failed to set Text mode")

    def test_cfun(self):
        self.logger.info("[gps_modem] Testing ME functionality (AT+CFUN?)...")
        # Page 26
        # https://nimbelink.com/Documentation/Skywire/4G_LTE_Cat_M1_Quectel/1002152_NL-SW-LTE-QBG96_QuickStartGuide.pdf
        out = self.ser.write('AT+CFUN?\r')
        if out.find('OK') != -1:
            start = out.find('+CFUN: ') + 7
            result = int(out[start:start + 1])
            if result != 1:
                self.logger.warning("[gps_modem] Got response %d (AT+CFUN?)...", result)
                raise IOError("Modem is not fully functional")
        else:
            self.logger.warning("Unexpected response: %s", out)
            out = self.ser.write('AT+CFUN=1\r')
            if out.find('OK') != -1:
                start = out.find('+CFUN: ')
                result = int(out[start + 6:])
                if result != 1:
                    self.logger.warning("[gps_modem] Got response %d (AT+CFUN?)...", result)
                    raise IOError("Modem is not fully functional")
            else:
                self.logger.error("[gps_modem] Failed to set ME functionality (AT+CFUN?)...")
                raise IOError("Modem is not fully functional")

    def test_qcsq(self):
        self.logger.info("[gps_modem] Testing query and report signal strength (AT+QCSQ)...")
        out = self.ser.write('AT+QCSQ\r')
        if out.find('OK') != -1:
            start = out.find('+QCSQ: ') + 7
            line = out[start:]
            self.logger.debug("line=%s", line)
            end = line.find('\r')
            self.logger.debug("end=%d", end)
            line = line[:end]
            parts = line.split(',')
            if parts[0] == "NOSERVICE":
                self.logger.error("[gps_modem] NOSERVICE mode reported")
                raise IOError("Modem has no service")
            else:
                self.logger.info("[gps_modem] Mode: %s (%s)", parts[0], parts[1])
        else:
            self.logger.error("Unexpected response: %s", out)
            self.logger.error("[gps_modem] Failed testing query and report signal strength (AT+QCSQ?)...")
            raise IOError("Modem has no service")

    def test_cereg(self):
        self.logger.info("[gps_modem] Testing EPS registration (AT+CEREG?)...")
        out = self.ser.write_wait('AT+CEREG?\r', 5)
        if out.find('OK') != -1:
            # +CEREG: 1,4
            start = out.find('+CEREG: ') + 8
            if start != -1:
                line = out[start:]
                self.logger.debug("line=%s", line)
                end = line.find('\r')
                self.logger.debug("end=%d", end)
                line = line[:end]
                parts = line.split(',')
                self.logger.debug("line=%s, parts=%s", line, parts)
                reg = int(parts[0])
                status = int(parts[1])
                if status == 0:
                    self.logger.info("[gps_modem] Modem is not registered, not currently searching for a new "
                                     "operator to register to - %s", line)
                    raise IOError("Modem is not registered")
                elif status == 1:
                    self.logger.info("[gps_modem] Modem is registered and on home network - %s", line)
                    return True
                elif status == 2:
                    self.logger.info("[gps_modem] Modem is not registered, but currently searching for a new "
                                     "operator to register to - %s", line)
                    raise IOError("Modem is not registered, searching")
                elif status == 3:
                    self.logger.info("[gps_modem] Registration denied - %s", line)
                    raise IOError("Modem registration denied")
                elif status == 4:
                    self.logger.info("[gps_modem] Modem is registered is unknown - %s", line)
                    return True
                elif status == 5:
                    self.logger.info("[gps_modem] Modem is registered and roaming - %s", line)
                    return True
                else:
                    self.logger.error("[gps_modem] Modem is not registered - %s (%d, %d)", line, reg, status)
                    raise IOError("Modem is not registered")
            else:
                self.logger.error("[gps_modem] Failed to get registration. out = %s", out)
                raise IOError("Failed to get registration")
        else:
            self.logger.error("[gps_modem] Failed to get registration. out = %s", out)
            raise IOError("Failed to get registration")

    def test_qiact(self, attempts):
        self.logger.info("[gps_modem] Querying PCP context (AT+QIACT?)...")
        out = self.ser.write_wait('AT+QIACT?\r', 5)
        if out.find('OK') != -1 & attempts < 2:
            # https://www.quectel.com/UploadImage/Downlad/Quectel_BG96_TCP(IP)_AT_Commands_Manual_V1.0.pdf
            start = out.find('+QIACT: ')
            if start != -1:
                line = out[start + 8:]
                self.logger.debug("line=%s", line)
                end = line.find('\r')
                self.logger.debug("end=%d", end)
                line = line[:end]
                parts = line.split(',')
                self.logger.debug("line=%s, parts=%s", line, parts)
                self.logger.info("[gps_modem] IP address is %s", parts[3])
                return True
            else:
                if self.activate_context():
                    self.test_qiact(attempts + 1)
                else:
                    self.logger.error("[gps_modem] Failed to activate PCP context (AT+QIACT?).")
                    raise IOError("Failed to activate PCP context")
        else:
            self.logger.error("[gps_modem] Failed to activate PCP context (AT+QIACT?). attempts = %d, out = %s",
                              attempts, out)
            raise IOError("Failed to activate PCP context")

    def activate_context(self):
        self.logger.info("[gps_modem] Attempting to active PCP context (AT+QIACT=1)...")
        out = self.ser.write_wait('AT+QIACT=1\r', 5)
        if out.find('OK') != -1:
            return True
        else:
            self.logger.error("[gps_modem] Failed to activate PCP context (AT+QIACT=1). out = %s", out)
            raise IOError("Failed to activate PCP context")

    def test_gps(self):
        self.logger.info("[gps_modem] Testing if GPS controller is powered up (AT+QGPS=1)...")
        out = self.ser.write('AT+QGPS?\r')
        if out.find('+QGPS: 1') == -1:
            self.logger.info("[gps_modem] Attempting to power-up GPS controller...")
            out = self.ser.write('AT+QGPS=1\r')
            if out.find('ERROR') != -1:
                self.logger.error("[gps_modem] Failed to enable GPS - %s", out)
                raise IOError("Failed to enable GPS")
            else:
                self.logger.info("[gps_modem] GPS is enabled")
        else:
            self.logger.info("[gps_modem] GPS is enabled")

    def get_rssi(self):
        try:
            out = self.ser.write('AT+CSQ\r')
            idx1 = out.find('+CSQ: ')
            if idx1 != -1:
                idx2 = out.index('\r\n\r\nOK\r\n')
                idx1 = idx1 + 6
                resp = out[idx1:idx2]
                [rssi, error] = resp.split(',')
                return int(rssi), int(error)
            else:
                self.logger.error("[gps_modem] Failed to get modem reception. %s", out)
                return -1, -1
        except Exception as ex:
            self.logger.exception("[gps_modem] Failed to read rssi information: %s", ex)
            return -1, -1

    def is_ok(self):
        out = self.ser.write('AT\r')
        if out.startswith('AT\r\nOK'):
            self.logger.error("[gps_modem] Modem did not report OK: %s", out)
            raise IOError("Modem did not report OK")

    def get_imsi(self):
        out = self.ser.write('AT+CIMI\r')
        i = "na"
        if out:
            idx2 = out.index('\r\n\r\nOK\r\n')
            i = out[10:idx2]
        return i

    def get_phone_number(self):
        out = self.ser.write('AT+CNUM\r')
        p = "unknown"
        if out.find('+CNUM:') != -1:
            line = out[7:]
            parts = line.split(',')
            start = parts[1].find('"') + 1
            end = parts[1][start:].find('"') + 1
            p = parts[1][start:end]
        else:
            self.logger.error("Failed to get context!")
        return p

    def get_ip(self):
        out = self.ser.write('AT+QIACT?\r')
        i = "unknown"
        if out.find('+QIACT:') != -1:
            line = out[8:]
            parts = line.split(',')
            start = parts[3].find('"') + 1
            end = parts[3][start:].find('"') + 1
            i = parts[3][start:end]
        else:
            self.logger.error("Failed to get context!")
        return i

    @staticmethod
    def decimal_degrees(degrees):
        return int(degrees / 100) + (degrees % 100) / 60

    def get_gps(self):
        out = self.ser.write('AT+QGPSLOC?\r')
        if len(out) < 9:
            self.logger.warning("[gps_modem] Getting GPS failure - unexpected response: %s", out)
            return {}

        if out.find('+QGPSLOC:') != -1:
            idx1 = out.index('+QGPSLOC:') + 9
            idx2 = out.index('\r\n\r\nOK\r\n')
            out = out[idx1:idx2].split(",")

            if len(out) < 5:
                self.logger.warning("[gps_modem] Getting GPS failure - unexpected response: %s", out)
                return {}

            if int(out[5]) == 1:
                self.logger.info("[gps_modem] No GPS signal...maybe warming up")
                return {}

            # Not ready reading:
            #
            # ['', '', '', '', '', '1', '', '', '', '', '']
            #
            # Good reading:
            #
            # ['042434.668', '3745.8152N', '12223.3605W', '1.00', '0.0', '3', '325.98', '0.04', '0.02', '291117', '07']

            self.logger.info("[gps_modem] Good GPS signal: lat=%s, lng=%s | out=%s", out[1][:-1], out[2][:-1], out)

            lat = self.decimal_degrees(float(out[1][:-1]))
            lat_ns = out[1][-1]
            if lat_ns == 'S':
                lat = -lat

            lng = self.decimal_degrees(float(out[2][:-1]))
            lng_ew = out[2][-1]
            if lng_ew == 'W':
                lng = -lng

            return {'ts': out[0], 'lat': lat, 'lat_ns': lat_ns, 'lng': lng, 'lng_ew': lng_ew, 'hdop': float(out[3]),
                    'alt': float(out[4]), 'fix': int(out[5]), 'cog': float(out[6]), 'spkm': float(out[7]),
                    'spkn': float(out[8]), 'date': out[9], 'nsats': int(out[10]), 'now': time.time()}
        elif out.find('+CME ERROR:') != -1:
            self.logger.info("[gps_modem] No satellite fix, please retry...")
        else:
            self.logger.error("[gps_modem] ERROR - unexpected response: %s", out)
        return {}

    def get_servinfo(self):
        try:
            # AT#RFSTS
            # #RFSTS: "310 260",686,-82,00FD,01,3,19,10,2,8AF3,"204043396525363","T-Mobile",3,4
            out = self.ser.write('AT#RFSTS\r')
            start = out.find('#RFSTS:')
            if start != -1:
                end = out.find(',', start)
                part = out[start:end]
                self.logger.info("[gps_modem] AT#RTSTS part = %s", part)
                [codes] = re.findall('"([^"]*)"', part)
                code_parts = codes.split(' ')

                # Its quoted :(
                mcc = int(code_parts[0])
                mnc = int(code_parts[1])
                self.logger.info("[gps_modem] Getting service information. mcc = %d, mnc = %d", mcc, mnc)
                return mcc, mnc
            else:
                return 0, 0
        except Exception as ex:
            self.logger.exception("[gps_modem] Failed get service info (AT#RFSTS). %s", ex)
            return 0, 0

    def get_cell_monitor(self):
        try:
            out = self.ser.write('AT#MONIZIP=7\r')
            cells = []
            if out.find('OK') != -1:
                out = self.ser.write_wait('AT#MONIZIP\r', 5)

                # AT#MONI
                # #MONI: Cell  BSIC  LAC  CellId  ARFCN    Power  C1  C2  TA  RxQual  PLMN
                # #MONI:  S    42  00FD   8AF3     686   -84dbm  19  19   0     0    T-Mobile
                # #MONI: N1    41  00FD   8AF5     760   -94dbm   9   9
                # #MONI: N2    FF  FFFF   0000     688  -111dbm  -1  -1
                # #MONI: N3    FF  FFFF   0000     687  -111dbm  -1  -1
                # #MONI: N4    FF  FFFF   0000     685  -111dbm  -1  -1
                # #MONI: N5    FF  FFFF   0000     758  -111dbm  -1  -1
                # #MONI: N6    FF  FFFF   0000     684  -111dbm  -1  -1
                #
                # OK

                self.logger.debug("OUT = %s", out)
                if out.find('OK') != -1:
                    lines = out.split('\r\n')
                    self.logger.debug("LINES = %s", lines)
                    found = 0
                    linecnt = 0
                    for line in lines:
                        linecnt = linecnt + 1
                        if linecnt == 1:
                            continue

                        self.logger.debug("line = %s", line)
                        if (line == 'OK') or (line == 'ERROR') or (line == ''):
                            break

                        line = line[10:]
                        parts = line.split(',')
                        self.logger.debug("PARTS = %s", parts)

                        # We want only valid cell towers
                        if parts[1] == 'FFFF':
                            self.logger.debug("[gps_modem] Cell report is null - %s", line)
                            continue

                        if parts[0] == '':
                            continue

                        # We only want the first good 3 cell towers
                        found = found + 1
                        if found > 3:
                            break

                        signal = 0
                        try:
                            signal = int(parts[4], 0)
                        except ValueError as ve:
                            self.logger.exception("Failed to parse signal - %s. Got %s", parts[4], ve)

                        lac = int('0x' + parts[1], 0)
                        cellid = int('0x' + parts[2], 0)
                        self.logger.info("[gps_modem] lac = %d (0x%s), cellid = %d (0x%s), signal = %d",
                                         lac, parts[1], cellid, parts[2], signal)
                        cells.append({'lac': lac, 'cellid': cellid, 'signal': signal})
                        self.logger.info("[gps_modem] cells = %s", cells)
            return cells
        except Exception as ex:
            self.logger.exception("[gps_modem] Failed during cell monitor. %s", ex)
            return []

    def write_pdu_message(self, recipient, binary_content):
        self.ser.write_pdu_message(recipient, binary_content)

    def write_message(self, recipient, text_content):
        self.ser.write_message(recipient, text_content)

    def unpack_msg(self, pdu):
        """Unpacks ``pdu`` into septets and returns the decoded string"""
        # Taken/modified from Dave Berkeley's pysms package
        self.logger.info("[gps_modem] parsing pdu message. pdu_msg = %s", pdu)
        count = last = 0
        result = []
        for i in range(0, len(pdu), 2):
            byte = int(pdu[i:i + 2], 16)
            mask = 0x7F >> count
            out = ((byte & mask) << count) + last
            last = byte >> (7 - count)
            result.append(out)
            if len(result) >= 0xa0:
                break
            if count == 6:
                result.append(last)
                last = 0
            count = (count + 1) % 7
        b = to_bytes(result)
        self.logger.info("[gps_modem] parsed pdu message. msg = %s", b)
        return b

    def pop_message(self):
        """
        This function will read the message from index position 1 and then delete it. Any other messages
        in storage will then move forward. Note: If SMS message mode is PDU, then None will be returned
        as the sender phone number
        :return:    message, sender
        """
        # AT+CMGR=1
        # +CMGR: 1,"",33
        # 07914180835760F0040B914180835760F000008121316101722B0FC8329BFD065DDF723619D4026501

        msg = None
        sender = None
        out = self.ser.write_wait('AT+CMGR=1\r', 5)
        start = out.find('+CMGR: ')
        if start != -1:
            self.logger.info("[gps_modem] MT PDU message 1 - %s", out)
            line = out[start + 7:]
            end = line.find('\r\n')
            line_end = end + 2
            if end == -1:
                end = line.find('\r\n\r\nOK')
                line_end = end + 6
                if end == -1:
                    self.logger.error("[gps_modem] No MT messages...")
                    return None, None

            if self.sms_mode == 0:
                self.logger.debug(">>>>> out = %s, line = %, end = %d", out, line, end)
                raw = line[:end]
                self.logger.debug("[gps_modem] pop_message raw = %s", raw)

                parts = raw.split('\r\n')
                self.logger.debug(">>>>> parts = %s:", parts)
                pdu_msg = parts[1][54:]
                msg = self.unpack_msg(pdu_msg)
            else:
                header = line[:end]
                msg_end = line.find('\r\n\r\nOK', line_end)
                msg = line[line_end:msg_end]

                parts = header.split(',')
                self.logger.info(">>>>> parts = %s", parts)
                sender = parts[1]
                self.logger.info(">>>>> out = %s, header = %s, body = %s, sender = %s", out, header, msg, sender)
                self.logger.info("[gps_modem] pop_message msg = %s, sender = %s", msg, sender)
            self.ser.write('AT+CMGD=1\r')
        else:
            self.logger.error("No messages to pop")
        return msg, sender

    def reset_modem(self):
        self.ser.reset_modem()

    def disconnect_phone(self):
        self.ser.close()

    def test_sms_service(self):
        out = ""
        try:
            # AT+CSMS?
            # +CSMS: 0,1,1,1
            out = self.ser.write('AT+CSMS?\r')
            start = out.find('+CSMS:') + 7
            if start != -1:
                end = out.find('\r\n', start)
                parts = out[start:end]
                self.logger.info("[gps_modem] AT+CSMS? parts = %s", parts)
                code_parts = parts.split(',')

                # Its quoted :(
                service = int(code_parts[0])
                mt = int(code_parts[1])
                mo = int(code_parts[1])
                bm = int(code_parts[1])
                self.logger.info("[gps_modem] Getting SMS support. service = %d, mt = %d, mo = %d, bm = %d",
                                 service, mt, mo, bm)
                if (mt == 1) and (mo == 1):
                    pass
                else:
                    raise IOError("SMS service does not support MO and MT messaging")
            else:
                raise IOError("SMS service does not support MO and MT messaging")
        except Exception as ex:
            self.logger.exception("[gps_modem] Failed get SMS support ('AT+CSMS?). %s - out = %s", ex, out)
            raise IOError("SMS service does not support MO and MT messaging.")


if __name__ == "__main__":
    gps_modem = GPSModem()
    imsi = gps_modem.get_imsi()
    ip = gps_modem.get_ip()
    phone = gps_modem.get_phone_number()

    print(">>> IMSI: {}, IP: {}, Phone: {}".format(imsi, ip, phone))

    while True:
        try:
            gps_dict = gps_modem.get_gps(),
            print(">>> %s" % gps_dict)
            time.sleep(5)
        except Exception as e:
            print("Failed to read GPS - %s " % e.message)
