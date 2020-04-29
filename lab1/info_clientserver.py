import logging, socket, threading

import constCS
#from context import lab_logging

#lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

GET_MSG_SIZE = 15
SIZE_MSG_SIZE = 10
ENTRY_SIZE = 40

class infoServer(threading.Thread):
    _logger = logging.getLogger("vs2lab.lab1.architecture.server")
    _serving = True
    telefondatenbank = \
        {"Pascal": "018054646",
         "Fabian": "01571234",
         "Konstantin": "01751234",
         "Tim": "49294",
         "Alexa": "29042020"}


    def __init__(self, *args, **kwargs):
        super(infoServer, self).__init__(*args, **kwargs)
        self._stopped = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((constCS.HOST, constCS.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))
        print("server started")

    def serve(self):
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                (connection, address) = self.sock.accept()  # returns new socket and address of client

                while True:  # forever
                    data = connection.recv(GET_MSG_SIZE)  # receive data from client
                    if not data:
                        break  # stop if client stopped
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

    def stop(self):
        print("setting stop")
        self._stopped.set()

    def isStopped(self):
        print("isStoppped")
        return self._stopped.is_set()

    def get(self, name, connection):
        num = self.telefondatenbank.get(name)
        msg = ("ENTRY " + str(name) + " " + str(num))
        msg = padding(msg, ENTRY_SIZE)
        connection.send(msg.encode('ascii'))

    def getAll(self, connection):
        metadata = str(len(self.telefondatenbank))
        msg = ("SIZE " + metadata)
        msg = padding(msg, SIZE_MSG_SIZE)
        connection.send(msg.encode('ascii'))
        for name, num in self.telefondatenbank.items():
            msg = ("ENTRY " + (str(name) + " " + str(num)))
            msg = padding(msg, ENTRY_SIZE)
            connection.send(msg.encode('ascii'))


class clientInterface:
    logger = logging.getLogger("vs2lab.a1_layers.architecture.client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((constCS.HOST, constCS.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))
        print("client started")

    def get(self, name):
        msg = ("GET " + name)
        msg = padding(msg, GET_MSG_SIZE)
        self.sock.send(msg.encode('ascii'))  #send GET request with parameter
        data = self.sock.recv(ENTRY_SIZE)  # receive entry
        msg_out = data.decode('ascii')
        msg_out = msg_out.split()[1] + ": " + msg_out.split()[2]
        #print(msg_out)
        return msg_out

    def getAll(self):
        msg = "GETALL"
        msg = padding(msg, GET_MSG_SIZE)
        self.sock.send(msg.encode('ascii'))  #send GETALL request without parameters
        metadata = self.sock.recv(SIZE_MSG_SIZE)  # receive metadata
        entries = int(metadata.split()[1])
        msg_list = []

        for i in range(0, entries):
            data = self.sock.recv(ENTRY_SIZE)     #receive entry
            msg_out = data.decode('ascii')
            msg_out = msg_out.split()[1] + ": " + msg_out.split()[2]
            msg_list.append(msg_out)
            #print(msg_out)
        return msg_list

    def close(self):
        self.sock.close()

def padding(existingMsg, size):
    while len(existingMsg) < size:  #for i in range(len(msg), size) ?
        existingMsg += " "
    return existingMsg


if __name__ == "__main__":
    print("---Main")
    # Create server in thread
    server = infoServer()
    serverThread = threading.Thread(target=server.serve)
    serverThread.start()

    # Create client
    client = clientInterface()
    result = client.get("Pascal")
    print(result)

    client.close()
    server.stop()