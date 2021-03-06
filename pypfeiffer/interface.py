""""""

# Standard library modules.
import atexit
import logging

# Third party modules.
import serial

# Local modules.

# Globals and constants variables.
CR = bytearray(b"\x0d")
LF = bytearray(b"\x0a")
ETX = bytearray(b"\x03")
ENQ = bytearray(b"\x05")
ACK = bytearray(b"\x06")
NAK = bytearray(b"\x15")


class PfeifferException(Exception):
    pass


class PfeifferSingleGaugeInterface(object):
    """
    Serial interface to Pfeiffer SingleGauge TPG 261 measurement and control 
    unit.
    """

    def __init__(self, comport="COM1", baudrate=9600):
        """
        Creates an interface.
        
        :arg comport: communication port (default: COM1)
        :arg baudrate: baudrate (default: 9600)
        """
        self._ser = serial.Serial(
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )
        self._ser.port = comport

        atexit.register(self._auto_disconnect)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def _auto_disconnect(self):
        if self.is_connected():
            self.disconnect()

    def is_connected(self):
        """
        Returns whether the interface is connected to the unit.
        """
        return self._ser.isOpen()

    def connect(self):
        """
        Connects.
        """
        if self.is_connected():
            raise PfeifferException("Already connected")
        self._ser.open()
        logging.debug("Serial connection opened")

        self._ser.flushInput()
        self._ser.flushOutput()
        logging.debug("Flush input and output")

    def disconnect(self):
        """
        Disconnects.
        """
        if not self.is_connected():
            raise PfeifferException("Not connected")
        self._ser.close()
        logging.debug("Serial connection closed")

    def reset(self):
        """
        Reset connection.
        """
        messages = {
            1: "Watchdog has responded",
            2: "Task fail error",
            3: "EPROM error",
            4: "RAM error",
            5: "EEPROM error",
            6: "DISPLAY error",
            7: "A/D converter error",
            9: "Gauge 1 error (e.g. filament rupture, no supply",
            10: "Gauge 1 identification error",
            11: "Gauge 2 error (e.g. filament rupture, no supply",
            12: "Gauge 2 identification error",
        }

        logging.debug("RES sent")
        self._ser.write(b"RES" + CR + LF)

        line = self._ser.readline().strip()
        if line != ACK:
            raise PfeifferException("Error sending 'RES'")

        logging.debug("ENQ sent")
        self._ser.write(ENQ)
        line = self._ser.readline().strip().decode("utf-8")
        statuses = map(int, line.split(","))

        errors = []
        for status in statuses:
            if status != 0:
                errors.append(messages[status])
        if errors:
            raise PfeifferException(
                "Following error(s) occurred: %s" % ", ".join(errors)
            )

    def pressure(self, gauge):
        """
        Returns pressure of specified gauge.
        """
        messages = {
            1: "Underrange",
            2: "Overrange",
            3: "Sensor error",
            4: "Sensor off",
            5: "No sensor",
            6: "Identification error",
        }

        logging.debug("PR%i sent", gauge)
        self._ser.write(bytearray("PR%i" % gauge, "ascii") + CR + LF)
        line = self._ser.readline().strip()
        if line != ACK:
            raise PfeifferException("Error sending 'PR%i'" % gauge)

        logging.debug("ENQ sent")
        self._ser.write(ENQ)
        line = self._ser.readline().strip().decode("utf-8")
        status, value = line.split(",")

        status = int(status)
        if status != 0:
            raise PfeifferException(messages[status])

        return float(value)

    @property
    def pressure_unit(self):
        """
        Returns/sets the pressure unit.
        Possible values:
        
            * bar
            * torr
            * pa
        """
        logging.debug("UNI sent")
        self._ser.write(b"UNI" + CR + LF)
        line = self._ser.readline().strip()
        if line != ACK:
            raise PfeifferException("Error sending 'UNI'")

        logging.debug("ENQ sent")
        self._ser.write(ENQ)
        line = self._ser.readline().strip().decode("utf-8")
        unit = int(line[0])

        return {0: "bar", 1: "torr", 2: "pa"}[unit]

    @pressure_unit.setter
    def pressure_unit(self, unit):
        if isinstance(unit, str):
            unit = {"bar": 0, "torr": 1, "pa": 2, "pascal": 2}[unit.lower()]
        unit = int(unit)

        logging.debug("UNI,%i sent", unit)
        self._ser.write(bytearray("UNI,%i" % unit, "ascii") + CR + LF)
        line = self._ser.readline().strip()
        if line != ACK:
            raise PfeifferException("Error sending 'UNI,%i'" % unit)

        logging.debug("ENQ sent")
        self._ser.write(ENQ)
        line = self._ser.readline().strip().decode("utf-8")
        newunit = int(line[0])

        if unit != newunit:
            raise PfeifferException("Unable to change pressure unit")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    with PfeifferSingleGaugeInterface("COM2") as p:
        p.reset()
        p.pressure_unit = "pa"
        print(p.pressure(1), p.pressure_unit)
