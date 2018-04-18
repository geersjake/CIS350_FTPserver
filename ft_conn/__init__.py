"""Module to handle transfer protocol and actual data transfer. Uses
ft_sock to provide network functionality.
"""

import enum
from pathlib import Path
from socket import timeout
from file_info import FileInfo
from .ft_sock import FTSock
from .ft_error import UnexpectedValueError

class FTProto:
    """Internally used to define control tokens for data transmission.
    """

    # Used to request the remote filelist.
    REQ_LIST = b'l'

    # Used to request a file. Following is a string of the file name/path
    REQ_FILE = b'f'

    # Used to send the filelist. Following is a '!i' representing the
    # number of entries, and then each entry is sent as a string (path),
    # '!32s?i' (hash digest, is_dir, and mtime int).
    RES_LIST = b'L'

    # Used to send the file. Following is a raw string of the contents of the file
    RES_FILE = b'F'

class FTConn:
    """Provides useful network functionality to be called by the UI.
    """

    # Keeps track of network versions. This is sent during the handshake,
    # to ensure compatibility
    _network_version = 1

    # Sent as handshake to make sure the other host is actually running
    # the program (response is it reversed). Must be 8 chars.
    _handshake_string = b'FTProtoW'

    def __init__(self, fts=None):
        """:param fts: FTSock object to use for connections. Constructs
            a new one if None or missing.
            :type fts: FTSock
        """
        if fts is None:
            self.fts = FTSock()
        else:
            self.fts = fts


    def __handshake(self, mode):
        """Conducts a handshake to ensure that the other host is running
            the same program, with a network protocol version that is
            compatible.

        :param mode: The role we are in the connection ("Client" if we
            connected to the other host, and "Server" if they connected
            to us).
        :type mode: string

        :return: Whether the handshake was successful.
        :rtype: boolean
        """

        if mode == "Client":
            self.fts.send_bytes(self._handshake_string)
            self.fts.send_int(self._network_version)

            alt_hs = self.fts.recv_bytes(8)
            alt_version = self.fts.recv_int()

            if alt_hs != self._handshake_string[::-1] or alt_version != self._network_version:
                return False

            return True


        else: # Assume mode == "Server"
            alt_hs = self.fts.recv_bytes(8)
            alt_version = self.fts.recv_int()

            self.fts.send_bytes(alt_hs[::-1])
            self.fts.send_int(self._network_version)

            if alt_hs != self._handshake_string or alt_version != self._network_version:
                return False

            return True

    def connect(self, host, port):
        """Initializes the connection to a remote host.

        :param host: Host to connect to (usually an IP).
        :type host: string

        :param port: Port to use for the connection (only applies for server).
        :type port: number

        :return: The status of the connection process (either "Success" or an
            error message).
        :rtype: string
        """

        connected, mode, message = self.fts.connect(host, port)

        if connected:
            self.fts.timeout_push(10)
            if not self.__handshake(mode):
                message = "Handshake failed"

        return message

    def send_file(self, file_data):
        """Sends file contents to other host.

        :param file_data: The file contents.
        :type file_data: raw string
        """

        self.fts.send_tok(FTProto.RES_FILE)
        self.fts.send_rstring(file_data)

    def send_file_list(self, file_list):
        """Sends the file list after a request.

        :param file_list: The file list to send (should be recently
            updated).
        :type file_list: list of FileInfo
        """

        self.fts.send_tok(FTProto.RES_LIST)

        list_length = len(file_list)
        self.fts.send_int(list_length)

        for file_info in file_list:
            self.fts.send_rstring(str(file_info.path).encode())
            self.fts.send_struct('!32s?Q', file_info.hash,
                                 file_info.is_dir,
                                 file_info.mtime)

    def request_file(self, filename):
        """Requests and receives a file from the other host.

        :param filename: The name of the file to request.
        :type filename: string

        :return: The contents of the file requested.
        :rtype: raw string

        :raises UnexpectedValueError: when the other host does
            not respond to our request properly.
        """

        self.fts.send_tok(FTProto.REQ_FILE)
        self.fts.send_rstring(filename.encode())

        self.__expect_tok((FTProto.RES_FILE,))

    def request_file_list(self):
        """Requests and receives a file list from the other host.

        :return: A list containing all of the file information requested.
        :rtype: list of FileInfo

        :raises UnexpectedValueError: when the other host does
            not respond to our request properly.
        """
        self.fts.send_tok(FTProto.REQ_LIST)



    def __receive_REQ_LIST(self):
        print("Received REQ_LIST")
        # TODO: Implement

    def __receive_REQ_FILE(self):
        fname = self.fts.recv_rstring().decode()
        print("Received REQ_FILE", fname)
        #TODO: Implement

    def __receive_RES_LIST(self):
        file_list = []
        for _ in range(self.fts.recv_int()):
            path = self.fts.recv_rstring().decode()
            (hashd, is_dir, mtime) = self.fts.recv_struct('!32s?Q')

            file_list.append(FileInfo(path=Path(path), file_hash=hashd, is_dir=is_dir, mtime=mtime))

        return file_list

    def __receive_RES_FILE(self):
        return self.fts.recv_rstring()
        

    def receive_data(self):
        self.fts.timeout_push(0)
        recv = self.fts.recv_bytes(1)
        self.fts.timeout_pop()
        if recv == FTProto.REQ_LIST:
            return recv, self.__receive_REQ_LIST()
        elif recv == FTProto.REQ_FILE:
            return recv, self.__receive_REQ_FILE()
        elif recv == FTProto.RES_LIST:
            return recv, self.__receive_RES_LIST()
        elif recv == FTProto.RES_FILE:
            return recv, self.__receive_RES_FILE()
        else:
            return None