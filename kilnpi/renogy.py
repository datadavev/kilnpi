import kilnpi.sensors
import renogy.btoneapp


class RenogyRover(kilnpi.sensors.BaseSensor):
    def __init__(
        self, group: str, name: str, mac_addr: str, adapter: str, interval: int
    ):
        super().__init__(group, name)
        self.adapter = adapter
        self.mac_addr = mac_addr
        self.device = renogy.btoneapp.BTOneApp(
            self.adapter,
            self.mac_addr,
            self.name,
            self.on_connected,
            self.on_data_received,
            interval,
        )
        self.last_data = None
        self.device.connect()

    def on_connected(self, app: renogy.btoneapp.BTOneApp):
        print("bt connected")
        app.poll_params()

    def on_data_received(self, app: renogy.btoneapp.BTOneApp, data):
        print(f"on data = {data}")
        self.last_data = data

    def get_point(self, **kwparams):
        if self.last_data is None:
            raise ValueError(f"No data available for {self.name}")
        point = (
            self._preget_point()
            .field("battery_percentage", self.last_data["battery_percentage"])
            .field("battery_voltage", self.last_data["battery_voltage"])
            .field("battery_amps", self.last_data["battery_amps"])
            .field("load_voltage", self.last_data["load_voltage"])
            .field("load_current", self.last_data["load_current"])
            .field("load_power", self.last_data["load_power"])
            .field("pv_voltage", self.last_data["pv_voltage"])
            .field("pv_current", self.last_data["pv_current"])
            .field("pv_power", self.last_data["pv_power"])
        )
        return point
