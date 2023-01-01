#!/usr/bin/python3

import argparse
import logging
import pprint
import threading

import debug
import http_api
import obis
import shared_sml_data
import sml
import sml_mqtt


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=str, default="/dev/ttyUSB0", help="Set serial device to use")
    parser.add_argument("--baudrate", type=int, default=9600, help="Set baudrate to use")
    parser.add_argument("--dump-file", type=str, default=None, help="Regularly dump SML structures/messages to a file")
    parser.add_argument("--dump-file-interval", type=int, default=10, help="How often should the SML data be dumped to file")
    parser.add_argument("--dump-console", default=False, action="store_true", help="Regularly dump OBIS data to console (if present in last SML reading)")
    parser.add_argument("--dump-console-interval", type=int, default=60, help="How often should the OBIS data be dumped to console")
    parser.add_argument("--mqtt-host", type=str, default=None, help="Set hostname/ip address of mqtt broker to connect to")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="Set port of mqtt broker to connect to")
    parser.add_argument("--mqtt-interval", type=int, default=30, help="How often should OBIS data be published to MQTT")
    parser.add_argument("--api-bind-ip", type=str, default="127.0.0.1", help="Bind HTTP API to this IP (0.0.0.0 binds to all available addresses)")
    parser.add_argument("--api-bind-port", type=int, default=5000, help="Bind HTTP API to this port")
    parser.add_argument("--debug", default=False, action="store_true", help="Enable debug output")
    return parser.parse_args()


def main():
    args = parse_arguments()
    log_format = "[%(levelname)s] [%(threadName)s] %(message)s"
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)

    sml_reader = threading.Thread(name="SerialReader", target=sml.read_serial_data, args=(args.device, args.baudrate,), daemon=True)
    logging.info("Starting SML reader thread")
    sml_reader.start()

    if args.dump_file is not None:
        logging.info("Starting periodic file dump thread (dumping every {} seconds)".format(args.dump_file_interval))
        file_dumper = threading.Thread(name="FileDumper", target=debug.dump_sml_data, args=(args.dump_file_interval, args.dump_file,), daemon=True)
        file_dumper.start()
    
    if args.dump_console:
        logging.info("Starting periodic console dump thread (dumping every {} seconds)".format(args.dump_console_interval))
        obis_dumper = threading.Thread(name="ConsoleDumper", target=debug.print_obis_data, args=(args.dump_console_interval,), daemon=True)
        obis_dumper.start()
    
    if args.mqtt_host is not None:
        logging.info("Starting mqtt publishing thread (publishing every {} seconds)".format(args.mqtt_interval))
        mqtt_publisher = threading.Thread(name="MqttPublisher", target=sml_mqtt.start_mqtt, args=(args.mqtt_host, args.mqtt_port, args.mqtt_interval), daemon=True)
        mqtt_publisher.start()

    logging.info("Starting API thread")
    api_thread = threading.Thread(name="HttpApi", target=http_api.start_api, args=(args.api_bind_ip, args.api_bind_port), daemon=True)
    api_thread.start()
    
    sml_reader.join()


if __name__ == "__main__":
    main()
