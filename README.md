# sml-reader <!-- omit in toc -->

This software reads and decodes SML / OBIS data from a serial device. It supports the following means of publishing the data:

- regularly dump OBIS datapoints to the console (debug)
- regulary dump SML structures to a textfile (debug)
- provide information through an HTTP API
  - dump the latest OBIS datapoints in JSON format
  - provide Prometheus scraping endpoint for the latest OBIS datapoints
- publish OBIS datapoints via MQTT

### Table of Contents <!-- omit in toc -->

- [Dependencies](#dependencies)
- [Tested Devices](#tested-devices)
- [OBIS Codes](#obis-codes)
- [HTTP API Routes](#http-api-routes)
  - [GET /obis-dump](#get-obis-dump)
  - [GET /metrics](#get-metrics)
- [MQTT publishing](#mqtt-publishing)
- [Getting sml-reader up and running](#getting-sml-reader-up-and-running)
  - [Example System Unit File](#example-system-unit-file)
- [Resources](#resources)

## Dependencies

- Python 3.7 or newer
- flask 1.0.2 or newer
- paho-mqtt 1.4.0 or newer

## Tested Devices

So far this software has been tested with the following meters:

- [EMH ED300L](https://emh-metering.com/en/products/domestic-meters-smart-meters/ed300l/)

## OBIS Codes

`sml-reader` has knowledge about a static set of OBIS datapoints (see [obis/__init__.py](obis/__init__.py)). It will always return all datapoints (e.g. via HTTP API). If your device does not provide these datapoints, their values will be set to `None` (Console output), `null` (JSON output) or `0` (Prometheus metrics). If you want to add new datapoints, you need to edit the Python code and add a) a type-code (`CODE_` variables) and b) a new entry to the `CODES` dictionary. You also need to know the OBIS bytecode so that it can be detected inside the SML data.

## HTTP API Routes

### GET /obis-dump

Provides all OBIS datapoints in JSON format. The dictionary keys used are internal representations of OBIS codes (see [obis/__init__.py](obis/__init__.py)). Example output:

```json
{
   "11" : {
      "internal_name" : "energy_total_l2",
      "description" : "Aktuelle Wirkleistung L2",
      "value" : null,
      "unit" : null,
      "type" : 3
   },
   "13" : {
      "internal_name" : "manufacturer",
      "description" : "Hersteller-Identifikation",
      "unit" : null,
      "value" : "ACME",
      "type" : 0
   }
}
```

### GET /metrics

Provides all OBIS datapoints in Prometheus' `text/plain` format (version 0.0.4). Example output:

```
# TYPE obis_energy_in_no_tariff counter
# HELP obis_energy_in_no_tariff Zaehlwerk pos. Wirkenergie (Bezug), tariflos, Einheit Wh
obis_energy_in_no_tariff{manufacturer="ACME",serial="12345-6789",serverid="aa-bb-cc-dd-ee-ff-11-22"} 58694.50
```

It will throw an HTTP 500 if no OBIS datapoints have been received (yet).

## MQTT publishing

`sml-reader` will construct the topic names from the data received via SML, using the manufacturer, serial and server-id:

```
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_in_no_tariff 12345.0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_in_tariff_1 12345.0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_in_tariff_2 0.0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_out_no_tariff 0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_out_tariff_1 0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_out_tariff_1 0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_current 140.05
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_total 0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_total_l1 0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_total_l2 0
sml/ACME/12345-6789/aa-bb-cc-dd-ee-ff-11-22/energy_total_l3 0
```

If either manufacturer, serial or serverid are unknown (e.g. not transmitted by the meter) they will be replaced by `unknown_manufacturer`, `unknown_serial` or `unknown_serverid`. You can check for data using the mosquitto client suite using the `+` or `#` wildcards:

```shell
# dump data from all topics
mosquitto_sub -h 127.0.0.1 -v -t "#"
# dump "energy_total" data from any manufacturer/serial/server-id
mosquitto_sub -h 127.0.0.1 -v -t "sml/+/+/+/energy_total"
# dump all topics from ACME meters
mosquitto_sub -h 127.0.0.1 -v -t "sml/ACME/+/+/+"
```

## Getting sml-reader up and running

By default, `sml-reader` will use `/dev/ttyUSB0` and a baudrate of 9600. You can change that with the `--device` and `--baudrate` parameters. If you have multiple USB serial adapters connected, I strongly advise you to use the unique representation of your device in `/dev/serial/by-id/` instead of `/dev/ttyUSBX` as the latter might not be consistent across reboots. `sml-reader` does **not** require root privileges to run! The serial devices usually belong to `root:dialout`, hence you might need to add yourself to the `dialout` group.

The HTTP API will bind to `127.0.0.1` on port `5000`. Use the `--api-bind-ip` and `--api-bind-port` parameters to override that. If you want to make the API publicy available (even "only" on your local network) I strongly advise you to use `apache`, `nginx` or `caddy` as a reverse proxy and add TLS and possibly authentication there.

If you want to get a quick glance at any received SML data structures, use `--debug` (to get the full debug/parsing output) or `--dump-file [path]` to get a dump of the latest SML structure received at a regular interval into the file specified with `[path]` (defaults to an interval 10 seconds).

If you want to get a quick glance at OBIS datapoints, you can use `--dump-console` (together with `--dump-console-interval`) to receive periodic OBIS dumps on the console.

To enable MQTT publishing you need to provide `sml-reader` with a hostname or IP address to connect to using `--mqtt-host [host]`. You can optionally override the MQTT default port (1883) using `--mqtt-port` and specify the interval in which OBIS data should be published using `--mqtt-interval`.

Whenever your meter emits an SML message, `sml-reader` should print the following to STDOUT:

```
[INFO] [SerialReader] Detected SML Start Sequence
```

If you do not see any of these messages, check the following:
- are you using the correct baud rate?
- are you using the correct device path?
- is your reading device positioned correctly?

You can also use `minicom` or `screen` to check your serial port settings. You should see incoming data every few seconds. However keep in mind that both tools will try to interpret the incoming data as text and hence display only gibberish.

### Example System Unit File
Place the follwing in `/etc/systemd/system/sml-reader.service` (you might need to extend the `ExecStart` line with additional command line parameters):

```
[Unit]
Description=SML message reader
After=network-online.target
Requires=network-online.target

[Service]
User=pi
ExecStart=/home/pi/edl300/sml-reader.py
Restart=on-abort

[Install]
WantedBy=multi-user.target
```

Then reload systemd, enable the service and start it:
```
systemctl daemon-reload
systemctl enable sml-reader
systemctl start sml-reader

# see whats happening:
journalctl -f -u sml-reader
```

## Resources

Most of these are only available in German language.

- [BSI "Smart Meter Language" documentation](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Publikationen/TechnischeRichtlinien/TR03109/TR-03109-1_Anlage_Feinspezifikation_Drahtgebundene_LMN-Schnittstelle_Teilb.pdf?__blob=publicationFile&v=1)
- [SML Wikipedia Article](https://de.wikipedia.org/wiki/Smart_Message_Language)
- [smldump Perl Script](https://github.com/hn/smldump)
- [libsml](https://github.com/volkszaehler/libsml)
- [libsml-testing](https://github.com/devZer0/libsml-testing)