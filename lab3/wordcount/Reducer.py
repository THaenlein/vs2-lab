# Task sink
# Binds PULL socket to tcp://localhost:5558
# Collects results from workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>

import sys
import time
import zmq
import pickle

import constPipe

me = str(sys.argv[1])

# Socket to receive messages on
port = constPipe.REDUCER1 if me == '1' else constPipe.REDUCER2
address = "tcp://" + constPipe.SENDER + ":" + port

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind(address)

print("Reducer ready.")

# Wait for start of batch
s = receiver.recv()

print("Reducer synchronized.")

# Process 100 confirmations
while True:
    word = pickle.loads(receiver.recv())
    print("Received word: {}".format(word))
