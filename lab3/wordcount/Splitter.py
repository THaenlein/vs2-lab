# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import pickle
import zmq
import random
import time

import constPipe

try:
    raw_input
except NameError:
    # Python 3
    raw_input = input

context = zmq.Context()

# Socket to send messages on
address = "tcp://" + constPipe.SENDER + ":" + constPipe.TASKS
sender = context.socket(zmq.PUSH)
sender.bind(address)

# Socket with direct access to the sink: used to synchronize start of batch
#address = "tcp://" + constPipe.SENDER + ":" + constPipe.RESULTS
#sink = context.socket(zmq.PUSH)
#sink.connect(address)

print("Reading file.")
with open("inputFile.txt") as file:
    content = file.readlines()
lines = [line.rstrip('\n') for line in content]

print("Press Enter when the workers are ready: ")
_ = raw_input()
print("Sending tasks to workers…")

# The first message is "0" and signals start of batch
#sink.send(b'0')

# Send 100 tasks
print("Sending {} workloads.".format(len(lines)))
for line in lines:
    sender.send(pickle.dumps(line))

# Give 0MQ time to deliver
time.sleep(1)
