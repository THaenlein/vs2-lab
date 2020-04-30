import logging
import threading
import unittest

import info_clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    _server = info_clientserver.InfoServer() # create a single server for all tests
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = info_clientserver.ClientInterface() # create new client before each test

    def test_clientGetValid(self):
        # Testing for a valid entry in the dictionary
        # Expected: Requested name and related telephone number
        result = self.client.get("Pascal")
        self.assertEqual(result, "Pascal: 018054646")

    def test_clientGetInvalid(self):
        # Testing for an invalid entry in the dictionary
        # Expected: Requested name and None
        result = self.client.get("Marvin")
        self.assertEqual(result, "Marvin: None")

    def test_clientGetOversized(self):
        # Testing for a name in the dictionary, which is greater than the ENTRY_SIZE
        # Expected: Different result than requested name and None
        result = self.client.get("Esenosarumensemwonken")
        self.assertNotEqual(result, "Esenosarumensemwonken: None")

    def test_clientGetAll(self):
        # Requesting every dictionary entries
        # Expected: Every single dictionary entry with corresponding telephone number as list
        telefondatenbank = ['Pascal: 018054646',
                            'Fabian: 01571234',
                            'Konstantin: 01751234',
                            'Tim: 49294',
                            'Alexa: 29042020']

        result = self.client.getAll()
        self.assertEqual(result, telefondatenbank)

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
