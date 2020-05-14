import rpc
import logging
import threading, time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

# Create list and call append function
base_list = rpc.DBList({'foo'})
thread = cl.append('bar', base_list, cl.responseReceived)

# Waiting for server response. Do something else.
while thread.isAlive():
    print("Waiting...")
    time.sleep(1)

print("Finished: terminating.")
cl.stop()
