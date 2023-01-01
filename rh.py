
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import math
import os
import socket
import time
import board
import adafruit_dht
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from ADCPi import ADCPi

INTERVAL = 10

org = "dave@vieglais.com"
client = influxdb_client.InfluxDBClient(
  url="https://us-east-1-1.aws.cloud2.influxdata.com",
  token=os.environ.get("INFLUXDB_TOKEN"),
  org=org
)
bucket="kiln"
write_api = client.write_api(write_options=SYNCHRONOUS)

adc_board = ADCPi(0x68, 0x69, 18)

def get_reference_voltage():
  return adc_board.read_voltage(4)


def get_ipaddress():
  ipaddr = None
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ipaddr = s.getsockname()[0]
    s.close()
  except Exception as e:
    print(e)
  return ipaddr

def saturatedVaporPressure(t):
  return 0.6108 * math.exp(17.27 * t / (t + 237.3))

def vaporPressure(t, rh):
  svp = saturatedVaporPressure(t)
  return svp * rh/100

class BaseSensor:
  def __init__(self, group: str, name:str):
    self.group = group
    self.name = name

  def _preget_point(self):
    return Point(self.group).tag("name", self.name)

  def get_point(self):
    point = (
      self._preget_point()
      .field("v", 0.0)
    )
    return point


class DHT22(BaseSensor):
  def __init__(self, pin, group:str, name:str):
    super().__init__(group, name)
    self.device = adafruit_dht.DHT22(pin)

  def get_point(self):
    tc = self.device.temperature
    rh = self.device.humidity
    point = (
      self._preget_point()
      .field("T", tc)
      .field("RH", rh)
      .field("VP", vaporPressure(tc,rh))
    )
    return point

class CurrentSensor(BaseSensor):
  def __init__(self, group:str, name:str, channel:int):
    super().__init__(group, name)
    self.channel = channel

  def get_point(self):
    # https://www.amazon.com/dp/B0BB8YN9ZJ?psc=1&ref=ppx_yo2ov_dt_b_product_details
    # 0 amp = vcc / 2
    # 66 mV / A
    v_ref = get_reference_voltage()
    v = adc_board.read_voltage(self.channel)
    v_0 = v_ref / 2.0
    amps = (v_0 - v) / 0.066
    return (
      self._preget_point()
      .field("v0", v_0)
      .field("v", v)
      .field("A", amps)
    )

def ip_point(group):
  ipaddr = get_ipaddress()
  return (
    Point(group)
    .tag("name", "ipaddr")
    .field("ip", ipaddr)
  )

sensors = []
group = "kiln"
sensors.append(DHT22(board.D17, group, name="HT-1"))
sensors.append(DHT22(board.D27, group, name="HT-2"))
sensors.append(DHT22(board.D22, group, name="HT-3"))
sensors.append(DHT22(board.D18, group, name="HT-4"))
sensors.append(CurrentSensor(group, "Fan-1", 1))
sensors.append(CurrentSensor(group, "Fan-2", 2))
sensors.append(CurrentSensor(group, "Fan-3", 3))
while True:
  for sensor in sensors:
    try:
      point = sensor.get_point()
      print(point)
      write_api.write(bucket=bucket, org=org, record=point)
    except RuntimeError as e:
      print(e)
  write_api.write(bucket=bucket, org=org, record=ip_point(group))
  time.sleep(INTERVAL)

