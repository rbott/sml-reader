import json
import threading
from flask import Flask, Response

import sml
import shared_sml_data
import obis

app = Flask(__name__)


@app.route('/obis-dump')
def api_obis_dump():
    lock = threading.Lock()
    with lock:
        if shared_sml_data.SML_RAW_DATA is not None:
            list_response = shared_sml_data.SML_RAW_DATA.GetRoot().GetListResponse()
            if list_response is not None:
                obis_data = sml.extract_obis_response_data(list_response)
                return json.dumps(obis_data)
    return json.dumps({})


@app.route('/metrics')
def api_prometheus_metrics():
    output = ""
    lock = threading.Lock()
    with lock:
        if shared_sml_data.SML_RAW_DATA is not None:
            list_response = shared_sml_data.SML_RAW_DATA.GetRoot().GetListResponse()
            if list_response is not None:
                obis_data = sml.extract_obis_response_data(list_response)
                manufacturer_data = obis_data[obis.CODE_MANUFACTURER]
                manufacturer = manufacturer_data["value"] if manufacturer_data["value"] is not None else "unknown manufacturer"
                
                serial_data = obis_data[obis.CODE_SERIAL]
                serial = serial_data["value"] if serial_data["value"] is not None else "unknown serial"
                
                serverid_data = obis_data[obis.CODE_ID]
                serverid = serverid_data["value"].replace(" ","-") if serverid_data["value"] is not None else "unknown server-id"
                for _, data in obis_data.items():
                    if data["type"] in [obis.TYPE_GAUGE, obis.TYPE_COUNTER]:
                        data_type = "gauge" if data["type"] == obis.TYPE_GAUGE else "counter"
                        value = 0 if data["value"] is None else data["value"]
                        
                        output += "# TYPE obis_{} {}\n".format(data["internal_name"], data_type)
                        output += "# HELP obis_{} {}, Einheit {}\n".format(data["internal_name"], data["description"], data["unit"])
                        output += "obis_{}{{manufacturer=\"{}\",serial=\"{}\",serverid=\"{}\"}} {:.2f}\n".format(data["internal_name"], manufacturer, serial, serverid, value)
    if output:
        return Response(output, content_type="text/plain; version=0.0.4;charset=UTF-8")
    else:
        return Response("No SML data (yet)", mimetype="text/plain", status=500)


def start_api(bind_ip, bind_port):
    app.run(host=bind_ip, port=bind_port)