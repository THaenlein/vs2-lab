import rpc
import logging
import threading, time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

# Creating client thread waiting for server response
callbackThread = threading.Thread(target=cl.responseReceived)
callbackThread.start()

base_list = rpc.DBList({'foo'})
cl.append('bar', base_list)

# Waiting for server response. Do something else.
while callbackThread.isAlive():
    print("Waiting...")
    time.sleep(1)

print("Finished: terminating.")
cl.stop()
