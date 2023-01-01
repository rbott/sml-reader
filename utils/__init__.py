
def hexlify(msg):
    # pretty-format byte arrays (space separated pairs of hex)
    hex_msg = msg.hex()
    return " ".join(a+b for a,b in zip(hex_msg[::2], hex_msg[1::2]))
