# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import os
import signal
import time
import board
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

import kilnpi.sensors
import kilnpi.renogy

TERMINATE = False
INTERVAL = 30

def main():
    org = "dave@vieglais.com"
    client = influxdb_client.InfluxDBClient(
        url="https://us-east-1-1.aws.cloud2.influxdata.com",
        token=os.environ.get("INFLUXDB_TOKEN"),
        org=org,
    )
    bucket = "kiln"
    adc_board = kilnpi.sensors.ADCBoard(0x68, 0x69, 18, reference=4)
    sensors = []
    group = "kiln"
    sensors.append(kilnpi.sensors.IPAddressSensor(group))
    sensors.append(
        kilnpi.renogy.RenogyRover(
            group,
            name="BT-TH-7724B9F3",
            mac_addr="F4:60:77:24:B9:F3",
            adapter="hci0",
            interval=INTERVAL,
        )
    )
    sensors.append(kilnpi.sensors.DHT22(board.D17, group, name="HT-1"))
    sensors.append(kilnpi.sensors.DHT22(board.D27, group, name="HT-2"))
    sensors.append(kilnpi.sensors.DHT22(board.D22, group, name="HT-3"))
    sensors.append(kilnpi.sensors.DHT22(board.D18, group, name="HT-4"))
    sensors.append(kilnpi.sensors.CurrentSensor(group, "Fan-1", adc_board, 1))
    sensors.append(kilnpi.sensors.CurrentSensor(group, "Fan-2", adc_board, 2))
    sensors.append(kilnpi.sensors.CurrentSensor(group, "Fan-3", adc_board, 3))
    while not TERMINATE:
        with client.write_api(
            write_options=influxdb_client.WriteOptions(
                batch_size=len(sensors),
                flush_interval=10_000,
                jitter_interval=2_000,
                retry_interval=5_000,
                max_retries=3,
                max_retry_delay=15,
                exponential_base=2,
            )
        ) as write_api:
            for sensor in sensors:
                try:
                    point = sensor.get_point()
                    print(point)
                    write_api.write(bucket=bucket, org=org, record=point)
                except RuntimeError as e:
                    print(e)
                except ValueError as e:
                    print(e)
        time.sleep(INTERVAL)
    for sensor in sensors:
        sensor.shutdown()

if __name__ == "__main__":
    main()
