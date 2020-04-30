import logging
import socket
import threading

import constCS
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init logging channels for the lab

ENTRY_KEYWORD = "Entry "
DICT_SIZE_KEYWORD = "Size "

REQUEST_MSG_SIZE = 15                            # Size of client requests
REPLY_MSG_SIZE = len(ENTRY_KEYWORD) + 35         # Size of server replies
METADATA_MSG_SIZE = len(DICT_SIZE_KEYWORD) + 5   # Message size of number of entries in phoneDirectory


class InfoServer(threading.Thread):
    _logger = logging.getLogger("vs2lab.lab1.info_clientserver.server")
    _serving = True
    _phoneDirectory = \
        {"Pascal": "018054646",
         "Fabian": "01571234",
         "Konstantin": "01751234",
         "Tim": "49294",
         "Alexa": "29042020"}

    # Initialization; Socket gets created and bound to address
    def __init__(self, *args, **kwargs):
        super(InfoServer, self).__init__(*args, **kwargs)
        self._stopped = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((constCS.HOST, constCS.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

    # Serving the client; Gets information requested by client
    def serve(self):
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                (connection, address) = self.sock.accept()  # returns new socket and address of client

                while True:  # forever
                    data = connection.recv(REQUEST_MSG_SIZE)  # receive data from client
                    if not data:
                        break  # stop if client stopped
                    self._logger.info("Server received message: \"" + str(data) + "\" from: " + str(address))
                    msg = data.decode('ascii')
                    if msg.startswith("GETALL"):  # case: return all entries
                        self.getAll(connection)
                    elif msg.startswith("GET"):   # case: return specific entry
                        name = msg.split()[1]
                        self.get(name, connection)
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts

            if self.isStopped():
                self.sock.close()
                self._logger.info("Server down.")
                return

        self.sock.close()
        self._logger.info("Server down.")

    # Sets flag for stopping thread
    def stop(self):
        self._stopped.set()

    def isStopped(self):
        return self._stopped.is_set()

    # Gets one entry from phoneDirectory
    def get(self, name, connection):
        num = self._phoneDirectory.get(name)
        msg = (ENTRY_KEYWORD + str(name) + " " + str(num))
        msg = fillLeftover(msg, REPLY_MSG_SIZE)
        connection.send(msg.encode('ascii'))
        self._logger.info("The following entry was sent to the client: " + str(msg))

    # Gets all entries from phoneDirectory
    def getAll(self, connection):
        metadata = str(len(self._phoneDirectory))
        msg = (DICT_SIZE_KEYWORD + metadata)
        msg = fillLeftover(msg, METADATA_MSG_SIZE)
        connection.send(msg.encode('ascii'))
        for name, num in self._phoneDirectory.items():
            msg = (ENTRY_KEYWORD + (str(name) + " " + str(num)))
            msg = fillLeftover(msg, REPLY_MSG_SIZE)
            connection.send(msg.encode('ascii'))
        self._logger.info("All entries were send to the client.")


# Client side and requests
class ClientInterface:
    logger = logging.getLogger("vs2lab.lab1.info_clientserver.client")

    # Connecting to socket
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((constCS.HOST, constCS.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    # Requesting for one entry from phoneDirectory
    def get(self, name):
        msg = ("GET " + name)
        msg = fillLeftover(msg, REQUEST_MSG_SIZE)
        self.sock.send(msg.encode('ascii'))  # send GET request with parameter
        self.logger.info("Client sent request: " + str(msg))
        data = self.sock.recv(REPLY_MSG_SIZE)  # receive entry
        msg_out = data.decode('ascii')
        self.logger.info("Client received reply: " + str(msg_out))
        msg_out = msg_out.split()[1] + ": " + msg_out.split()[2]
        return msg_out

    # Requesting for all entries from phoneDirectory
    def getAll(self):
        msg = "GETALL"
        msg = fillLeftover(msg, REQUEST_MSG_SIZE)
        self.sock.send(msg.encode('ascii'))  # send GETALL request without parameters
        self.logger.info("Client sent request: " + str(msg))
        metadata = self.sock.recv(METADATA_MSG_SIZE)  # receive number of entries
        entries = int(metadata.split()[1])
        self.logger.info("Reply will contain this amount of entries: " + str(entries))
        msg_list = []

        for i in range(0, entries):
            data = self.sock.recv(REPLY_MSG_SIZE)     # receive entry
            msg_out = data.decode('ascii')
            msg_out = msg_out.split()[1] + ": " + msg_out.split()[2]
            msg_list.append(msg_out)
        self.logger.info("Client received reply: \"" + str(msg_list))
        return msg_list

    # Close socket
    def close(self):
        self.sock.close()
        self.logger.info("Client socket closed.")


def fillLeftover(existingMsg, size): # used to assure specific message size for requests and replies
    return existingMsg + (" " * (size-len(existingMsg)))


if __name__ == "__main__":
    # Create server as thread
    server = InfoServer()
    serverThread = threading.Thread(target=server.serve)
    serverThread.start()

    # Create client
    client = ClientInterface()

    # Send get request
    result = client.get("Pascal")
    print(result)

    # Send get request
    result = client.get("Fabian")
    print(result)

    # Send get request
    result = client.get("Konstantin")
    print(result)

    # Send get request
    result = client.get("Tim")
    print(result)

    # Send get request
    result = client.get("Alexa")
    print(result)

    # Send getAll request
    result = client.getAll()
    print(result)

    # Close connection and terminate thread
    client.close()
    server.stop()
