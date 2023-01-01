
import logging
import serial
import threading

import obis
import shared_sml_data
import utils

LISTS = []

ESCAPE_SEQ =b"\x1b\x1b\x1b\x1b" 
START_SEQ = ESCAPE_SEQ + b"\x01\x01\x01\x01"
END_SEQ = b"\x1b\x1b\x1b\x1b\x1a"

MASK_EXTENDED_TYPE = 0x80
MASK_TYPE = 0x70
MASK_LENGTH = 0x0F

TYPE_LIST = 0x70
TYPE_OCTET_STRING = 0x00
TYPE_SIGNED_INT = 0x50
TYPE_UNSIGNED_INT = 0x60
TYPE_BOOL = 0x40

class SML_Octet_String():
    length = 0
    data = None
    parent = None
    
    def __init__(self, length, data, parent):
        self.length = length
        self.data = data
        self.parent = parent
    
    def __repr__(self):
        obis_str = obis.BytesToString(self.data)
        if obis_str:
            obis_str = " (OBIS Code: '{}')".format(obis_str)
        return "{}: SML Octet String: {}{}".format(hex(id(self)), utils.hexlify(self.data), obis_str)


class SML_Signed_Integer():
    length = 0
    data = None
    parent = None
    
    def __init__(self, length, data, parent):
        self.length = length
        self.data = data
        self.parent = parent
    
    def __repr__(self):
        return "{}: SML Signed Int: {}".format(hex(id(self)), self.data)


class SML_Unsigned_Integer():
    length = 0
    data = None
    parent = None
    
    def __init__(self, length, data, parent):
        self.length = length
        self.data = data
        self.parent = parent
    
    def __repr__(self):
        return "{}: SML Unsigned Int: {}".format(hex(id(self)), self.data)


class SML_End_of_Message():
    parent = None
    
    def __init__(self, parent):
        self.parent = None
    
    def __repr__(self):
        return "{}: SML End-of-Message Element".format(hex(id(self)))


class SML_Structure():
    parent = None
    length = None
    children = []
    BODY_TYPES = {
        0x0100: "Open.Request",
        0x0101: "Open.Response",
        0x0200: "Close.Request",
        0x0201: "Close.Response",
        0x0300: "GetProfilePack.Request",
        0x0301: "GetProfilePack.Response",
        0x0400: "GetProfileList.Request",
        0x0401: "GetProfileList.Response",
        0x0500: "GetProcParameter.Request",
        0x0501: "GetProcParameter.Response",
        0x0600: "SetProcParameter.Request",
        0x0601: "SetProcParameter.Response",
        0x0700: "GetList.Request",
        0x0701: "GetList.Response",
        0x0800: "GetCosemRequest",
        0x0801: "GetCosemResponse",
        0x0900: "SetCosemRequest",
        0x0901: "SetCosemResponse",
        0x0a00: "ActionCosem.Request",
        0x0a01: "ActionCosem.Response",
        0xff01: "Attentation.Response"
    }
    
    def __init__(self, length=None, parent=None):
        self.parent = parent
        self.length = length
        self.children = []
    
    def __repr__(self):
        if self.parent is None:
            parent = "None"
        else:
            parent = hex(id(self.parent))
        return "{}: SML_Structure: parent {}, length {}, children {}, SML-Type {}".format(hex(id(self)), parent, self.length, len(self.children), self.GetStructureTypeString())
    
    def returnSelfOrParent(self):
        if self.length is not None and len(self.children) > self.length:
            raise Exception("Error: structure contains more elements ({}) than allowed ({})".format(len(self.children), self.length))
        if self.parent is not None and len(self.children) == self.length:
            return self.parent.returnSelfOrParent()
        return self
    
    def AddStructure(self, length):
        newStructure = SML_Structure(length, self)
        self.children.append(newStructure)
        return newStructure
    
    def AddOctetString(self, length, data):
        self.children.append(SML_Octet_String(length, data, self))
        return self.returnSelfOrParent()
    
    def AddSignedInteger(self, length, data):
        self.children.append(SML_Signed_Integer(length, data, self))
        return self.returnSelfOrParent()
    
    def AddUnsignedInteger(self, length, data):
        self.children.append(SML_Unsigned_Integer(length, data, self))
        return self.returnSelfOrParent()
    
    def AddEndOfMessage(self):
        self.children.append(SML_End_of_Message(self))
        return self.returnSelfOrParent()
    
    def GetRoot(self):
        if self.parent is None:
            return self
        return self.parent.GetRoot()

    def RecursiveDump(self):
        sb = []
        return self._RecursiveDump(sb)

    def _RecursiveDump(self, sb, indentation=""):
        for child in self.children:
            sb.append("{}{}".format(indentation, child))
            if isinstance(child, SML_Structure):
                indentation = indentation + " "
                child._RecursiveDump(sb, indentation)
                indentation = indentation[0:-1]
        return sb
       
    def RecursiveLog(self, indentation=""):
        logging.debug("%s%s", indentation, self)
        for child in self.children:
            if isinstance(child, SML_Structure):
                indentation = indentation + " "
                child.RecursiveLog(indentation)
                indentation = indentation[0:-1]
            else:
                logging.debug("%s%s", indentation, child)
    
    def GetListResponse(self):
        message_body = self._RecursiveGetListResponse()
        if message_body is not None:
            return message_body.children[1]
        return None
    
    def _RecursiveGetListResponse(self):
        for child in self.children:
            if isinstance(child, SML_Structure):
                if child.GetStructureTypeString() == "GetList.Response":
                    return self
                element = child._RecursiveGetListResponse()
                if element is not None:
                    return element
    
    # the following function is more of hack to find OBIS
    # data nested anywhere in a SML structure
    def RecursiveObisFind(self, obis_code):
        for child in self.children:
            if isinstance(child, SML_Octet_String):
                if child.data == obis_code:
                    return child.parent
            elif isinstance(child, SML_Structure):
                element = child.RecursiveObisFind(obis_code)
                if element is not None:
                    return element
    
    def GetStructureTypeString(self):
        if self.parent is None:
            return "File"
        if self.children and isinstance(self.children[-1], SML_End_of_Message):
            return "Message"
        if len(self.children) == 2 and isinstance(self.children[0], SML_Unsigned_Integer) and isinstance(self.children[1], SML_Structure):
            return "MessageBody"
        if self.parent.GetStructureTypeString() == "MessageBody" and self.parent.children[0].data in self.BODY_TYPES:
            return self.BODY_TYPES[self.parent.children[0].data]

        return "Unknown"


def log_with_indent(*msg):
    logging.debug("%s%s", len(LISTS) *  " ", *msg)


def get_field_length(msg, pos):
    length = msg[pos] & MASK_LENGTH
    additional_bytes_read = 0
    # detect extended TL byte
    # that means we need to add the length part of the following byte
    if msg[pos] & MASK_EXTENDED_TYPE == 0x80:
        pos += 1
        additional_bytes_read += 1
        # shift the rightmost bits four to the left
        length = (length << 4) & 0xFF
        # 'or' the length-part of the next byte to the bit-shiftet length
        length = length | (msg[pos] & MASK_LENGTH)
    return length - additional_bytes_read, pos


def parse_sml_bytestream(msg, footer):
    global LISTS
    shared_sml_data.SML_RAW_DATA = SML_Structure()
    fill_byte_counter = int(footer[1])
    logging.debug("Number of Fill Bytes: %d", fill_byte_counter)
    # strip fill-bytes off the end
    if fill_byte_counter > 0:
        msg = msg[:fill_byte_counter * -1]
    checksum = footer[2:]
    pos = 0
    try:
        while True:
            # reached end of the message? bye
            if pos >= len(msg):
                break
            # track nested structures (only relevant for debug output)
            if LISTS:
                if LISTS[-1] <= 0:
                    LISTS.pop()
                LISTS[-1] -= 1
            
            # detect "End of SML Message" byte
            if msg[pos] == 0x00:
                log_with_indent("End of SML Message")
                LISTS = []
                pos += 1
                shared_sml_data.SML_RAW_DATA = shared_sml_data.SML_RAW_DATA.AddEndOfMessage()
            # detect list / sequence TL byte
            elif msg[pos] & MASK_TYPE == TYPE_LIST:
                length, pos = get_field_length(msg, pos)
                log_with_indent("List Element {}".format(length))
                LISTS.append(length)
                shared_sml_data.SML_RAW_DATA = shared_sml_data.SML_RAW_DATA.AddStructure(length)
                pos += 1
            # detect octet string TL byte
            elif msg[pos] & MASK_TYPE == TYPE_OCTET_STRING:
                length, pos = get_field_length(msg, pos)
                oct_string = msg[pos + 1:pos + length]
                log_with_indent("Octet String {} {} {}".format(length - 1, utils.hexlify(oct_string), obis.BytesToString(oct_string)))
                shared_sml_data.SML_RAW_DATA = shared_sml_data.SML_RAW_DATA.AddOctetString(length, oct_string)
                pos += length
            # detect signed int TL byte
            elif msg[pos] & MASK_TYPE == TYPE_SIGNED_INT:
                length, pos = get_field_length(msg, pos)
                int_buf = msg[pos + 1:pos + length]
                signed_int = int.from_bytes(int_buf, byteorder="big", signed=True)
                log_with_indent("Signed Int {} {} {}".format(length - 1, utils.hexlify(int_buf), signed_int))
                shared_sml_data.SML_RAW_DATA = shared_sml_data.SML_RAW_DATA.AddSignedInteger(length, signed_int)
                pos += length
            # detect unsigned int TL byte
            elif msg[pos] & MASK_TYPE == TYPE_UNSIGNED_INT:
                length, pos = get_field_length(msg, pos)
                uint_buf = msg[pos + 1:pos + length]
                unsigned_int = int.from_bytes(uint_buf, byteorder="big", signed=False)
                log_with_indent("Unsigned Int {} {} {}".format(length - 1, utils.hexlify(uint_buf), unsigned_int))
                shared_sml_data.SML_RAW_DATA = shared_sml_data.SML_RAW_DATA.AddUnsignedInteger(length, unsigned_int)
                pos += length
            # detect boolean TL byte
            elif msg[pos] & MASK_TYPE == TYPE_BOOL:
                length, pos = get_field_length(msg, pos)
                pos += 1
                if msg[pos] == 0x00:
                    bool_data = False
                else:
                    bool_data = True
                log_with_indent("Bool {} {} {}".format(length, msg[pos], bool_data))
                pos += 1
            else:
                raise Exception("Unknown Field Type found: {} at position {}, remaining msg: '{}'".format(msg[pos], pos, utils.hexlify(msg[pos:])))
    except IndexError as e:
        print("Tried to parse beyond end of message (position {}, message length {})".format(pos, len(msg)))
    finally:
        LISTS = []
    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        shared_sml_data.SML_RAW_DATA.GetRoot().RecursiveLog()


def read_serial_data(device, baudrate):
    sel = serial.Serial(port=device, baudrate=baudrate, timeout=2, rtscts=False, dsrdtr=False)
    buffer = b''
    start_seq_complete = False
    received_msg = False
    while True:
        data = sel.read(1)
        if data is None:
            continue
        buffer = buffer + data
        if buffer.find(START_SEQ) > -1 and not start_seq_complete:
            logging.info("Detected SML Start Sequence")
            start_seq_complete = True
            received_msg = False
            if len(buffer) > len(START_SEQ):
                logging.debug("Found extra data ahead of Start Sequence: %s", utils.hexlify(buffer[:-len(START_SEQ)]))
            buffer = b''
            continue
        if start_seq_complete and buffer.endswith(ESCAPE_SEQ):
            sml_msg = buffer[0:-len(ESCAPE_SEQ)] 
            logging.debug("Detected SML Message Body: %s", utils.hexlify(sml_msg))
            buffer = b''
            start_seq_complete = False
            received_msg = True
            continue
        if received_msg and len(buffer) >= 4 and buffer.find(b"\x1a") == 0:
            sml_footer = buffer
            logging.debug("Detected SML Message Footer: %s", utils.hexlify(sml_footer))
            lock = threading.Lock()
            with lock:
                parse_sml_bytestream(sml_msg, sml_footer)
            buffer = b""
            received_msg = False
            continue


def extract_obis_response_data(response):
    data = {}
    for code, item in obis.CODES.items():
        obis_data_structure = response.children[4]
        value = None
        unit = None
        for child in obis_data_structure.children:
            if child.children[0].data != item["bytes"]:
                continue
            if item["type"] == obis.TYPE_STRING:
                try:
                    value = child.children[5].data.decode("utf-8")
                except UnicodeDecodeError:
                    logging.error("Could not decode UTF-8 string for OBIS code '{}'".format(item["description"]))
                    value = ""
            elif item["type"] in [obis.TYPE_GAUGE, obis.TYPE_COUNTER]:
                scaler = 10 ** child.children[4].data
                value = child.children[5].data * scaler
                unit = obis.GetUnitFromCode(child.children[3].data)
            elif item["type"] == obis.TYPE_BINARY:
                value = utils.hexlify(child.children[5].data)
        data[code] = {
            "description": item["description"],
            "internal_name": item["internal_name"],
            "unit": unit,
            "value": value,
            "type": item["type"],
        }
    return data