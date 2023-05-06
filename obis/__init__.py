
CODE_UNKNOWN = -1
CODE_SERIAL = 0
CODE_ID = 1
CODE_ENERGY_IN_NO_TARIFF = 2
CODE_ENERGY_IN_TARIFF_1 = 3
CODE_ENERGY_IN_TARIFF_2 = 4
CODE_ENERGY_OUT_NO_TARIFF = 5
CODE_ENERGY_OUT_TARIFF_1 = 6
CODE_ENERGY_OUT_TARIFF_2 = 7
CODE_ENERGY_CURRENT = 8
CODE_ENERGY_TOTAL = 9
CODE_ENERGY_TOTAL_L_1 = 10
CODE_ENERGY_TOTAL_L_2 = 11
CODE_ENERGY_TOTAL_L_3 = 12
CODE_MANUFACTURER = 13
CODE_PUBLIC_KEY = 14

TYPE_STRING = 0
TYPE_COUNTER = 1
TYPE_GAUGE = 3
TYPE_BINARY = 4

UNITS = {
    1: "Y",
    2: "M",
    3: "W",
    4: "D",
    5: "H",
    6: "M",
    7: "S",
    8: "°",
    9: "°C",
    10: "¤",
    11: "m",
    12: "m/s",
    13: "m³",
    14: "m³ (corr)",
    15: "m³/h",
    16: "m³/h (corr)",
    17: "m³/d",
    18: "m³/d (corr)",
    19: "l",
    20: "kg",
    21: "N",
    22: "Nm",
    23: "Pa",
    24: "bar",
    25: "J",
    26: "J/h",
    27: "W",
    28: "VA",
    29: "var",
    30: "Wh",
    31: "VAh",
    32: "varh",
    33: "A",
    34: "C",
    35: "V",
    36: "V/m",
    37: "F",
    38: "Ω",
    39: "Ωm²/m",
    40: "Wb",
    41: "T",
    42: "A/m",
    43: "H",
    44: "Hz",
    45: "1/(Wh)",
    46: "1/(varh)",
    47: "1/(VAh)",
    48: "V²h",
    49: "A²h",
    50: "kg/s",
    51: "mho",
    52: "K",
    53: "1/(V²h)",
    54: "1/(A²h)",
    55: "1/m³",
    56: "%",
    57: "Ah",
    60: "Wh/m³",
    61: "J/m³",
    62: "Mol%",
    63: "g/m³",
    64: "Pa s",
    65: "J/kg",
    70: "dBm",
    71: "dBµV",
    72: "dB",
    255: "count",
}

CODES = {
    CODE_MANUFACTURER: {
        "bytes": b"\x81\x81\xC7\x82\x03\xFF",
        "description": "Hersteller-Identifikation",
        "internal_name": "manufacturer",
        "type": TYPE_STRING,
    },
    CODE_SERIAL: {
        "bytes": b"\x00\x00\x60\x01\xFF\xFF",
        "description": "Seriennummer",
        "internal_name": "serial",
        "type": TYPE_STRING,
    },
    CODE_ID: {
        "bytes": b"\x01\x00\x00\x00\x09\xFF",
        "description": "Server-ID",
        "internal_name": "server_id",
        "type": TYPE_BINARY,
    },
    CODE_ENERGY_IN_NO_TARIFF: {
        "bytes": b"\x01\x00\x01\x08\x00\xFF",
        "description": "Zaehlwerk pos. Wirkenergie (Bezug), tariflos",
        "internal_name": "energy_in_no_tariff",
        "type": TYPE_COUNTER,
    },
    CODE_ENERGY_IN_TARIFF_1: {
        "bytes": b"\x01\x00\x01\x08\x01\xFF",
        "description": "Zaehlwerk pos. Wirkenergie (Bezug), Tarif 1",
        "internal_name": "energy_in_tariff_1",
        "type": TYPE_COUNTER,
    },
    CODE_ENERGY_IN_TARIFF_2: {
        "bytes": b"\x01\x00\x01\x08\x02\xFF",
        "description": "Zaehlwerk pos. Wirkenergie (Bezug), Tarif 2",
        "internal_name": "energy_in_tariff_2",
        "type": TYPE_COUNTER,
    },
    CODE_ENERGY_OUT_NO_TARIFF: {
        "bytes": b"\x01\x00\x02\x08\x00\xFF",
        "description": "Zaehlwerk neg. Wirkenergie (Einspeisung), tariflos",
        "internal_name": "energy_out_no_tariff",
        "type": TYPE_COUNTER,
    },
    CODE_ENERGY_OUT_TARIFF_1: {
        "bytes": b"\x01\x00\x02\x08\x01\xFF",
        "description": "Zaehlwerk neg. Wirkenergie (Einspeisung), Tarif 1",
        "internal_name": "energy_out_tariff_1",
        "type": TYPE_COUNTER,
    },
    CODE_ENERGY_OUT_TARIFF_2: {
        "bytes": b"\x01\x00\x02\x08\x02\xFF",
        "description": "Zaehlwerk neg. Wirkenergie (Einspeisung), Tarif 2",
        "internal_name": "energy_out_tariff_2",
        "type": TYPE_COUNTER,
    },
    CODE_ENERGY_CURRENT: {
        "bytes": b"\x01\x00\x0F\x07\x00\xFF",
        "description": "Betrag der aktuellen Wirkleistung",
        "internal_name": "energy_current",
        "type": TYPE_GAUGE,
    },
    CODE_ENERGY_TOTAL: {
        "bytes": b"\x01\x00\x10\x07\x00\xFF",
        "description": "Aktuelle Wirkleistung gesamt",
        "internal_name": "energy_total",
        "type": TYPE_GAUGE,
    },
    CODE_ENERGY_TOTAL_L_1: {
        "bytes": b"\x01\x00\x24\x07\x00\xFF",
        "description": "Aktuelle Wirkleistung L1",
        "internal_name": "energy_total_l1",
        "type": TYPE_GAUGE,
    },
    CODE_ENERGY_TOTAL_L_2: {
        "bytes": b"\x01\x00\x38\x07\x00\xFF",
        "description": "Aktuelle Wirkleistung L2",
        "internal_name": "energy_total_l2",
        "type": TYPE_GAUGE,
    },
    CODE_ENERGY_TOTAL_L_3: {
        "bytes": b"\x01\x00\x4c\x07\x00\xFF",
        "description": "Aktuelle Wirkleistung L3",
        "internal_name": "energy_total_l3",
        "type": TYPE_GAUGE,
    },
    CODE_PUBLIC_KEY: {
        "bytes": b"\x81\x81\xC7\x82\x05\xFF",
        "description": "Public Key",
        "internal_name": "public_key",
        "type": TYPE_BINARY,
    },
}


def BytesToString(byte_stream):
    for code_id, code in CODES.items():
        if code["bytes"] == byte_stream:
            return code["description"]
    return ""


def GetUnitFromCode(code):
    if code in UNITS:
        return UNITS[code]
    return None