import threading
import time
import logging

import sml
import shared_sml_data
import obis


def dump_sml_data(interval, file_path):
    # add some initial wait here
    time.sleep(2)
    while True:
        if shared_sml_data.SML_RAW_DATA is not None:
            lock = threading.Lock()
            with lock:
                with open(file_path, "w") as fout:
                    logging.info("Dumping current SML data to {}".format(file_path))
                    data = "\n".join(shared_sml_data.SML_RAW_DATA.GetRoot().RecursiveDump()) + "\n"
                    fout.write(data)
        time.sleep(interval)


def print_obis_data(interval):
    # add some initial wait here
    time.sleep(2)
    while True:
        lock = threading.Lock()
        with lock:
            if shared_sml_data.SML_RAW_DATA is not None:
                list_response = shared_sml_data.SML_RAW_DATA.GetRoot().GetListResponse()
                if list_response is not None:
                    obis_data = sml.extract_obis_response_data(list_response)
                    print("Dumping OBIS data to console")
                    for _, data in obis_data.items():
                        if data["unit"] is None:
                            print(" {}: {}".format(data["description"], data["value"]))
                        else:
                            print(" {}: {}{}".format(data["description"], data["value"], data["unit"]))
                    print()
                else:
                    logging.debug("Could not print any OBIS data - none found in the last SML message")
        time.sleep(interval)
