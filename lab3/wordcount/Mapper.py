import pickle
import sys
import zmq
import re

import constPipe

me = str(sys.argv[1])

context = zmq.Context()

# Socket to receive messages on
address = "tcp://" + constPipe.SENDER + ":" + constPipe.TASKS
receiver = context.socket(zmq.PULL)
receiver.connect(address)

# Socket to send messages to
address1 = "tcp://" + constPipe.SENDER + ":" + constPipe.REDUCER1
address2 = "tcp://" + constPipe.SENDER + ":" + constPipe.REDUCER2
reducer1 = context.socket(zmq.PUSH)
reducer2 = context.socket(zmq.PUSH)
reducer1.connect(address1)
reducer2.connect(address2)

print("Worker {} ready.".format(me))

# Process tasks forever
while True:
    sentence = pickle.loads(receiver.recv())
    print("{} got sentence: {}".format(me, sentence))

    # Do the work
    words = re.findall(r"[\w]+", sentence)
    print("Splitted in {} words.".format(len(words)))

    # Send results to reducer
    for word in words:
        if len(word) < 4:
            reducer1.send(pickle.dumps(word))
        else:
            reducer2.send(pickle.dumps(word))
