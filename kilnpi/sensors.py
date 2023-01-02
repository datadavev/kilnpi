import math

import ADCPi
import adafruit_dht
from influxdb_client import InfluxDBClient, Point, WritePrecision

import kilnpi


def saturatedVaporPressure(t: float) -> float:
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def vaporPressure(t: float, rh: float) -> float:
    svp = saturatedVaporPressure(t)
    return svp * rh / 100


class ADCBoard(ADCPi.ADCPi):
    def __init__(self, *params, **kwparams):
        try:
            self.reference_channel = kwparams["reference"]
            kwparams.pop("reference")
        except KeyError:
            self.reference_channel = 4
        super().__init__(*params, **kwparams)

    def reference_voltage(self):
        return self.read_voltage(self.reference_channel)


class BaseSensor:
    def __init__(self, group: str, name: str):
        self.group = group
        self.name = name

    def _preget_point(self):
        return Point(self.group).tag("name", self.name)

    def get_point(self, **kwparams):
        point = self._preget_point().field("v", 0.0)
        return point


class IPAddressSensor(BaseSensor):
    def __init__(self, group: str):
        super().__init__(group, "ipaddr")

    def get_point(self, **kwparams):
        ipaddress = kilnpi.get_ipaddress()
        return self._preget_point().field("ip", ipaddress)


class DHT22(BaseSensor):
    def __init__(self, pin, group: str, name: str):
        super().__init__(group, name)
        self.device = adafruit_dht.DHT22(pin)

    def get_point(self, **kwparams):
        tc = self.device.temperature
        rh = self.device.humidity
        point = (
            self._preget_point()
            .field("T", tc)
            .field("RH", rh)
            .field("VP", vaporPressure(tc, rh))
        )
        return point


class CurrentSensor(BaseSensor):
    def __init__(self, group: str, name: str, adc_board: ADCBoard, channel: int):
        super().__init__(group, name)
        self.adc_board = adc_board
        self.channel = channel

    def get_point(self, **kwparams):
        # https://www.amazon.com/dp/B0BB8YN9ZJ?psc=1&ref=ppx_yo2ov_dt_b_product_details
        # 0 amp = vcc / 2
        # 66 mV / A

        v_ref = self.adc_board.reference_voltage()
        v = self.adc_board.read_voltage(self.channel)
        v_0 = v_ref / 2.0
        amps = (v_0 - v) / 0.066
        return self._preget_point().field("v0", v_0).field("v", v).field("A", amps)
