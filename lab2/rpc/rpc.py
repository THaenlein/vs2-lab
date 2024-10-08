import constRPC
import time, threading

from context import lab_channel


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


# Client inheriting from Thread
class Client(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        self.chan.leave('client')

    def append(self, data, db_list, callbackFunction):
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server
        result = self.chan.receive_from(self.server, timeout=3)
        if result[1] == constRPC.OK:
            callbackThread = threading.Thread(target=callbackFunction)
            callbackThread.start()
            return callbackThread
        else:
            print("Not acknowledged!")
            return None

    # Callback function waiting for server response
    def responseReceived(self):
        msgrcv = self.chan.receive_from(self.server)  # wait for response
        print("Result: {}".format(msgrcv[1].value))


class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    ack = constRPC.OK
                    self.chan.send_to({client}, ack)
                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    time.sleep(10)
                    self.chan.send_to({client}, result)  # return response
                else:
                    pass  # unsupported request, simply ignore