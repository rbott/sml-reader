
# init shared variable 
# SML/read thread will fill this variable with data, all other threads will read from it
# you _must_ use threading.Lock() while accessing SML_DATA to ensure the integrity of the data
SML_RAW_DATA = None

