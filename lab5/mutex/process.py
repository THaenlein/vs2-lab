import logging
import random
import time

from constMutex import ENTER, RELEASE, ALLOW, ALIVE


class Process:
    """
    Implements access management to a critical section (CS) via fully
    distributed mutual exclusion (MUTEX).

    Processes broadcast messages (ENTER, ALLOW, RELEASE) timestamped with
    logical (lamport) clocks. All messages are stored in local queues sorted by
    logical clock time.

    A process broadcasts an ENTER request if it wants to enter the CS. A process
    that doesn't want to ENTER replies with an ALLOW broadcast. A process that
    wants to ENTER and receives another ENTER request replies with an ALLOW
    broadcast (which is then later in time than its own ENTER request).

    A process enters the CS if a) its ENTER message is first in the queue (it is
    the oldest pending message) AND b) all other processes have sent messages
    that are younger (either ENTER or ALLOW). RELEASE requests purge
    corresponding ENTER requests from the top of the local queues.

    Message Format:

    <Message>: (Timestamp, Process_ID, <Request_Type>)

    <Request Type>: ENTER | ALLOW  | RELEASE

    """

    def __init__(self, chan):
        self.channel = chan  # Create ref to actual channel
        self.process_id = self.channel.join('proc')  # Find out who you are
        self.all_processes: list = []  # All procs in the proc group
        self.other_processes: list = []  # Needed to multicast to others
        self.queue = []  # The request queue list
        self.processes_alive = []
        self.last_ping = dict()
        self.clock = 0  # The current logical clock
        self.logger = logging.getLogger("vs2lab.lab5.mutex.process.Process")

    # Extract processId from mapId and return actual process
    # param mapId: String
    #       "Proc_*" Possible Values are: A, B, C ...
    def extractProcessIdentifier(self, mapId):
        lastChar = mapId[-1]
        # This is a terrible way of determining the index
        # Maybe there's the root of the problem
        index = ord(lastChar) - 65
        # TODO: Fix "List index out of range"
        return self.all_processes[index]

    def cleanUpQueueAfterCrash(self):
        newQueue = []
        # Check if process_id of queued messages is in processes list
        for message in self.queue:
            if message[1] in self.all_processes:
                newQueue.append(message)
        self.queue = newQueue
        self.__cleanup_queue()

    def pingAlive(self):
        self.clock += 1
        message = (self.clock, self.process_id, ALIVE)
        self.channel.send_to(self.other_processes, message)

    def __mapid(self, id='-1'):
        # resolve channel member address to a human friendly identifier
        if id == '-1':
            id = self.process_id
        return 'Proc_' + chr(65 + self.all_processes.index(id))

    def __cleanup_queue(self):
        if len(self.queue) > 0:
            #self.queue.sort(key = lambda tup: tup[0])
            self.queue.sort()
            # There should never be old ALLOW messages at the head of the queue
            while self.queue[0][2] == ALLOW:
                del (self.queue[0])
                if len(self.queue) == 0:
                    break

    def __request_to_enter(self):
        self.clock = self.clock + 1  # Increment clock value
        request_msg = (self.clock, self.process_id, ENTER)
        self.queue.append(request_msg)  # Append request to queue
        self.__cleanup_queue()  # Sort the queue
        self.channel.send_to(self.other_processes, request_msg)  # Send request

    def __allow_to_enter(self, requester):
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, ALLOW)
        self.channel.send_to([requester], msg)  # Permit other

    def __release(self):
        # need to be first in queue to issue a release
        assert self.queue[0][1] == self.process_id, 'State error: inconsistent local RELEASE'

        # construct new queue from later ENTER requests (removing all ALLOWS)
        tmp = [r for r in self.queue[1:] if r[2] == ENTER]
        self.queue = tmp  # and copy to new queue
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, RELEASE)
        # Multicast release notification
        self.channel.send_to(self.other_processes, msg)

    def __allowed_to_enter(self):
        # See who has sent a message
        processes_with_later_message = set([req[1] for req in self.queue[1:]])
        # Access granted if this process is first in queue and all others have answered (logically) later
        first_in_queue = self.queue[0][1] == self.process_id
        all_have_answered = len(self.other_processes) == len(processes_with_later_message)
        return first_in_queue and all_have_answered

    def __receive(self):
         # Pick up any message
        _receive = self.channel.receive_from(self.other_processes, 10) 
        if _receive:
            msg = _receive[1]
            sender = self.__mapid(_receive[0])

            self.clock = max(self.clock, msg[0])  # Adjust clock value...
            self.clock = self.clock + 1  # ...and increment

            self.last_ping[sender] = msg[0]

            self.logger.debug("{} received {} from {}.".format(
                self.__mapid(),
                "ENTER" if msg[2] == ENTER
                else "ALLOW" if msg[2] == ALLOW
                else "RELEASE" if msg[2] == RELEASE
                else "ALIVE",
                self.__mapid(msg[1])))

            if msg[2] == ENTER:
                self.queue.append(msg)  # Append an ENTER request
                # and unconditionally allow (don't want to access CS oneself)
                self.__allow_to_enter(msg[1])
            elif msg[2] == ALLOW:
                self.queue.append(msg)  # Append an ALLOW
            elif msg[2] == RELEASE:
                # assure release requester indeed has access (his ENTER is first in queue)
                assert self.queue[0][1] == msg[1] and self.queue[0][2] == ENTER, 'State error: inconsistent remote RELEASE'
                if len(self.queue) > 0:
                    del (self.queue[0])  # Just remove first message

            self.__cleanup_queue()  # Finally sort and cleanup the queue
        else:
            self.logger.warning("{} timed out on RECEIVE.".format(self.__mapid()))
            timedOutProcesses = []
            # Iterate over last pings and check who didn't send alive since last check.
            # Remove those processes from lists and clean queue
            # Reset ping for processes that recently sent one
            for process, ping in self.last_ping.items():
                #print("Process {} has ping {}.".format(process, ping))
                if ping == 0:
                    processId = self.extractProcessIdentifier(process)
                    # Sometimes a process removes itself from the list. wtf?
                    # Maybe use different functions to extract processId for self.other_processes and self.all_processes
                    print("Process {} removes process {} from list ".format(self.__mapid()[-1], process[-1]))
                    self.other_processes.remove(processId)
                    self.all_processes.remove(processId)
                    timedOutProcesses.append(process)
                else:
                    self.last_ping[process] = 0

            for crashedProcess in timedOutProcesses:
                del self.last_ping[crashedProcess]

            self.cleanUpQueueAfterCrash()
            self.pingAlive()

    def init(self):
        self.channel.bind(self.process_id)

        self.all_processes = list(self.channel.subgroup('proc'))
        # sort string elements by numerical order
        self.all_processes.sort(key=lambda x: int(x))

        self.other_processes = list(self.channel.subgroup('proc'))
        self.other_processes.remove(self.process_id)

        # Set initial pings for other processes
        for otherProcess in self.other_processes:
            self.last_ping[self.__mapid(otherProcess)] = self.clock

        self.logger.info("Member {} joined channel as {}."
                         .format(self.process_id, self.__mapid()))

    def run(self):
        while True:
            # Enter the critical section if there are more than one process left
            # and random is true
            if len(self.all_processes) > 1 and \
                    random.choice([True, False]):
                self.logger.debug("{} wants to ENTER CS at CLOCK {}."
                    .format(self.__mapid(), self.clock))

                self.__request_to_enter()
                while not self.__allowed_to_enter():
                    self.__receive()

                # Stay in CS for some time ...
                sleep_time = random.randint(0, 2000)
                self.logger.debug("{} enters CS for {} milliseconds."
                    .format(self.__mapid(), sleep_time))
                print(" CS <- {}".format(self.__mapid()))
                time.sleep(sleep_time/1000)

                # ... then leave CS
                print(" CS -> {}".format(self.__mapid()))
                self.__release()
                continue

            # Occasionally serve requests to enter (
            if random.choice([True, False]):
                self.__receive()
