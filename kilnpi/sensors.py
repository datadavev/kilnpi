import math

import ADCPi
import adafruit_dht
from influxdb_client import InfluxDBClient, Point, WritePrecision
import numpy as np

import kilnpi


def saturatedVaporPressure(t: float) -> float:
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def vaporPressure(t: float, rh: float) -> float:
    # kPa
    svp = saturatedVaporPressure(t)
    return svp * rh / 100


def absoluteHumidity(t: float, rh: float) -> float:
    # g / m3
    return (6.112 * math.exp((17.67*t)/(t+243.5)) * rh * 2.1674) / (273.15+t)


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

class SensorField:
    def __init__(self):
        self.value = None

    def setValue(self, v):
        self.value = v

    def getValue(self):
        return self.value


class NumericSensorField(SensorField):
    #TODO: need to mask out of range values
    #TODO: value is the last unmasked value
    #TODO: roll the list when at end
    def __init__(self, label:str, history_length=10, dtype:str=np.float64):
        super().__init__()
        self.cpos = 0
        self.value = np.zeros(history_length, dtype=dtype)

    def getValue(self):
        return


class BaseSensor:
    def __init__(self, group: str, name: str, fields: list[SensorField]=None):
        self.group = group
        self.name = name
        self.fields = fields
        if self.fields is None:
            self.fields = {}

    def shutdown(self):
        pass

    def _preget_point(self):
        return Point(self.group).tag("name", self.name)

    def update(self):
        # override this to set the value of each field
        pass

    def get_point(self, **kwparams):
        self.update()
        point = self._preget_point()
        for k,v in self.fields.items():
            point = point.field(k, v.getValue())
        return point


class IPAddressSensor(BaseSensor):
    def __init__(self, group: str):
        super().__init__(group, "ipaddr")
        self.fields = {"ip":SensorField()}

    def update(self):
        ipaddress = kilnpi.get_ipaddress()
        self.fields["ip"].setValue(ipaddress)


class DHT22(BaseSensor):
    def __init__(self, pin, group: str, name: str):
        super().__init__(group, name)
        self.device = adafruit_dht.DHT22(pin)
        self.fields = {
            "T": SensorField(),
            "RH": SensorField(),
            "VP": SensorField(),
            "AH": SensorField(),
            "VPD": SensorField(),
        }

    def update(self):
        tc = self.device.temperature
        rh = self.device.humidity
        self.fields["T"].setValue(tc)
        self.fields["RH"].setValue(rh)
        svp = saturatedVaporPressure(tc)
        vp = vaporPressure(tc, rh)
        self.fields["VP"].setValue(vp)
        self.fields["VPD"].setValue(svp-vp)
        self.fields["AH"].setValue(absoluteHumidity(tc, rh))


class CurrentSensor(BaseSensor):
    def __init__(self, group: str, name: str, adc_board: ADCBoard, channel: int):
        super().__init__(group, name)
        self.adc_board = adc_board
        self.channel = channel
        self.fields = {
            "v0": SensorField(),
            "v": SensorField(),
            "A": SensorField(),
        }

    def update(self):
        # https://www.amazon.com/dp/B0BB8YN9ZJ?psc=1&ref=ppx_yo2ov_dt_b_product_details
        # 0 amp = vcc / 2
        # 66 mV / A
        v_ref = self.adc_board.reference_voltage()
        v = self.adc_board.read_voltage(self.channel)
        v_0 = v_ref / 2.0
        amps = (v_0 - v) / 0.066
        self.fields["v0"].setValue(v_0)
        self.fields["v"].setValue(v)
        self.fields["A"].setValue(amps)

