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

INTERVAL = 30

org = "dave@vieglais.com"
client = influxdb_client.InfluxDBClient(
  url="https://us-east-1-1.aws.cloud2.influxdata.com",
  token=os.environ.get("INFLUXDB_TOKEN"),
  org=org
)
bucket="dht22_test"
write_api = client.write_api(write_options=SYNCHRONOUS)

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

class DHT22:
  def __init__(self, pin, name:str):
    self.device = adafruit_dht.DHT22(pin)
    self.name=name

  def get_point(self):
    tc = self.device.temperature
    rh = self.device.humidity
    point = (
      Point("test")
      .tag("name", self.name)
      .field("T", tc)
      .field("RH", rh)
      .field("VP", vaporPressure(tc,rh))
    )
    return point

def ip_point():
  ipaddr = get_ipaddress()
  return (
    Point("test")
    .tag("name", "ipaddr")
    .field("ip", ipaddr)
  )

sensors = []
sensors.append(DHT22(board.D17, name="HT-1"))
sensors.append(DHT22(board.D18, name="HT-2"))
sensors.append(DHT22(board.D19, name="HT-3"))
while True:
  for sensor in sensors:
    try:
      point = sensor.get_point()
      print(point)
      write_api.write(bucket=bucket, org=org, record=point)
    except RuntimeError as e:
      print(e)
  write_api.write(bucket=bucket, org=org, record=ip_point())
  time.sleep(INTERVAL)

