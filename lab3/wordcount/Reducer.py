import sys
import zmq
import pickle
from collections import Counter

import constPipe

me = str(sys.argv[1])

# Socket to receive messages on
port = constPipe.REDUCER1 if me == '1' else constPipe.REDUCER2
address = "tcp://" + constPipe.SENDER + ":" + port

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind(address)

wordCount = Counter()

print("Reducer ready.")

# Count words
while True:
    word = pickle.loads(receiver.recv())
    if word == '\r':
        wordCount.clear()
        print("Resetting counter.")
    else:
        wordCount[word] += 1
        print("Received word \"{}\": {}".format(word, wordCount[word]))