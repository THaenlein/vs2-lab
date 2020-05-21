import pickle
import zmq
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

# Socket with direct access to both reducers: used to reset word count
address = "tcp://" + constPipe.SENDER + ":" + constPipe.REDUCER1
reducer1 = context.socket(zmq.PUSH)
reducer1.connect(address)
address = "tcp://" + constPipe.SENDER + ":" + constPipe.REDUCER2
reducer2 = context.socket(zmq.PUSH)
reducer2.connect(address)

print("Reading file.")
with open("inputFile.txt") as file:
    content = file.readlines()
lines = [line.rstrip('\n') for line in content]

print("Press Enter when the workers are ready: ")
_ = raw_input()
print("Sending tasks to workers…")

# Reset word count in reducers
reducer1.send(pickle.dumps('\r'))
reducer2.send(pickle.dumps('\r'))

# Send 100 tasks
print("Sending {} workloads.".format(len(lines)))
for line in lines:
    sender.send(pickle.dumps(line))

# Give 0MQ time to deliver
time.sleep(1)
