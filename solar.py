import logging 
from renogy.BTOneApp import BTOneApp 

logging.basicConfig(level=logging.DEBUG)

# [f4:60:77:24:b9:f3] Discovered, alias = BT-TH-7724B9F3
ADAPTER = "hci0"
MAC_ADDR = "F4:60:77:24:B9:F3"
DEVICE_ALIAS = "BT-TH-7724B9F3"
POLL_INTERVAL = 30 # read data interval (seconds)

def on_connected(app: BTOneApp):
    app.poll_params() # OR app.set_load(1)

def on_data_received(app: BTOneApp, data):
    logging.debug("{} => {}".format(app.device.alias(), data))
    # app.disconnect() # disconnect here if you do not want polling

bt1 = BTOneApp(ADAPTER, MAC_ADDR, DEVICE_ALIAS, on_connected, on_data_received, POLL_INTERVAL)
bt1.connect()
