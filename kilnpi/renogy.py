import logging
import threading
import kilnpi.sensors
import renogy.btoneapp

_L = logging.getLogger(__name__)


class RenogyRoverCollector(threading.Thread):
    def __init__(self, device=None):
        super().__init__()
        self.device = device

    def disconnect(self):
        self.device.disconnect()

    def run(self):
        self.device.connect()


class RenogyRover(kilnpi.sensors.BaseSensor):
    def __init__(
        self, group: str, name: str, mac_addr: str, adapter: str, interval: int
    ):
        super().__init__(group, name)
        self.fields = {
            "battery_percentage": kilnpi.sensors.SensorField(),
            "battery_voltage": kilnpi.sensors.SensorField(),
            "battery_current": kilnpi.sensors.SensorField(),
            "load_voltage": kilnpi.sensors.SensorField(),
            "load_current": kilnpi.sensors.SensorField(),
            "load_power": kilnpi.sensors.SensorField(),
            "pv_voltage": kilnpi.sensors.SensorField(),
            "pv_current": kilnpi.sensors.SensorField(),
            "pv_power": kilnpi.sensors.SensorField(),
        }
        self.adapter = adapter
        self.mac_addr = mac_addr
        device = renogy.btoneapp.BTOneApp(
            self.adapter,
            self.mac_addr,
            self.name,
            self.on_connected,
            self.on_data_received,
            interval,
        )
        self.worker = RenogyRoverCollector(device=device)
        self.last_data = None
        self.worker.start()

    def shutdown(self):
        _L.info("Renogy bt disconnected")
        self.worker.disconnect()

    def on_connected(self, app: renogy.btoneapp.BTOneApp):
        _L.info("Renogy bt connected")
        app.poll_params()

    def on_data_received(self, app: renogy.btoneapp.BTOneApp, data):
        self.last_data = data
        for k in self.fields:
            self.fields[k].setValue(self.last_data[k])

    def update(self):
        # updates are handled in the worker thread
        pass

    def get_point(self, **kwparams):
        if self.last_data is None:
            raise ValueError(f"No data available for {self.name}")
        return super().get_point(**kwparams)
