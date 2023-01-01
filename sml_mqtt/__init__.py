import paho.mqtt.client as mqtt
import logging
import time
import threading

import sml
import shared_sml_data
import obis

def connect(host, port):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT broker")
        else:
            logging.warn("Failed to connect to MQTT broker")
    logging.info("Connecting to {}:{}".format(host, port))
    client = mqtt.Client("sml-reader")
    client.on_connect = on_connect
    client.connect(host, port, 60)
    return client

def start_mqtt(host, port, interval):
    client = connect(host, port)
    time.sleep(5)
    while True:
        lock = threading.Lock()
        with lock:
            if shared_sml_data.SML_RAW_DATA is not None:
                list_response = shared_sml_data.SML_RAW_DATA.GetRoot().GetListResponse()
                if list_response is not None:
                    logging.info("Publishing OBIS data to MQTT")
                    obis_data = sml.extract_obis_response_data(list_response)
                    manufacturer_data = obis_data[obis.CODE_MANUFACTURER]
                    manufacturer = manufacturer_data["value"] if manufacturer_data["value"] is not None else "unknown_manufacturer"
                    
                    serial_data = obis_data[obis.CODE_SERIAL]
                    serial = serial_data["value"] if serial_data["value"] is not None else "unknown_serial"
                    
                    serverid_data = obis_data[obis.CODE_ID]
                    serverid = serverid_data["value"].replace(" ","-") if serverid_data["value"] is not None else "unknown_serverid"
                    for _, data in obis_data.items():
                        if data["type"] in [obis.TYPE_GAUGE, obis.TYPE_COUNTER]:
                            value = 0 if data["value"] is None else data["value"]
                            
                            topic = "sml/{}/{}/{}/{}".format(manufacturer, serial, serverid, data["internal_name"])
                            msg = value
                            logging.debug("{}: {}".format(topic, msg))
                            client.publish(topic, msg)
                else:
                    logging.warn("Could not publish any OBIS data - none found in the last SML message")
            else:
                logging.warn("Could not publish any OBIS data - no SML data received (yet)")
        time.sleep(interval)
