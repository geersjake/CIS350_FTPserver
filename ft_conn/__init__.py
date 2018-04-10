"""Module to handle transfer protocol and actual data transfer. Uses
ft_sock to provide network functionality.

:Authors: Colton Bates
"""

import enum
from pathlib import Path
from socket import timeout
from file_info import FileInfo
from .ft_sock import FTSock
from .ft_error import UnexpectedValueError, BrokenSocketError

class FTProto(enum.Enum):
    """Internally used to define control tokens for data transmission.
    """

    # Used to request the remote filelist.
    REQ_LIST = b'l'

    # Used to request a file. Following is a string of the file name/path
    REQ_FILE = b'f'

    # Used to represent a lack of requests and invalid tokens, respectively.
    REQ_NONE = b'None'
    TINVALID = b'Invalid'

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

    @staticmethod
    def __gtv(tok_val):
        """Converts a raw char to a control token.

        :param tok_val: The string value of some token in FTProto.
        :type tok_val: raw string (1 char length)

        :return: The enum equivalent of the token.
        :rtype: FTProto
        """

        # Horrifying hack to check equality to enum
        reqtoks = [tok for tok in FTProto if tok.value == tok_val]

        if len(reqtoks) != 1:
            return FTProto.TINVALID

        return reqtoks[0]

    def __expect_tok(self, toktuple):
        """Receives a token and ensures that it was one that we expected.

        :param toktuple: A tuple containing every possible token that we
            expect.
        :type toktuple: tuple of FTProto

        :return: The token we actually received.
        :rtype: FTProto

        :raises UnexpectedValueError: when we receive a token we were not
            expecting.
        """

        try:
            tokr = self.fts.recv_bytes(1)
        except timeout:
                                          # For some reason pylint doesn't think
                                          # FTProto.<x>.value is of type bytes,
                                          # but it is, so we need to ignore the error
            tokr = FTProto.REQ_NONE.value # pylint: disable = redefined-variable-type


        tok = self.__gtv(tokr)

        if tok not in toktuple:
            tokrs = tok.value

            raise UnexpectedValueError(str(toktuple), str(tokrs))

        return tok

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

    def check_for_request(self):
        """Checks the network buffer to see if there are any requests
        we need to respond to.

        :return: FTProto.REQ_LIST, FTProto.REQ_FILE, or FTProto.REQ_NONE.
            If FTProto.REQ_FILE, also the filename requested, otherwise None.
        :rtype: FTProto, string

        :raises UnexpectedValueError: when we receive an invalid request.
        """

        self.fts.timeout_push(0.1)
        req = self.__expect_tok((FTProto.REQ_FILE, FTProto.REQ_LIST, FTProto.REQ_NONE))
        self.fts.timeout_pop()

        if req == FTProto.REQ_FILE:
            fname = self.fts.recv_rstring().decode()
        else:
            fname = None

        return req, fname

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
            self.fts.send_struct('!32s?i', file_info.hash,
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

        return self.fts.recv_rstring()

    def request_file_list(self):
        """Requests and receives a file list ffrom the other host.

        :return: A list containing all of the file information requested.
        :rtype: list of FileInfo

        :raises UnexpectedValueError: when the other host does
            not respond to our request properly.
        """

        file_list = []


        self.fts.send_tok(FTProto.REQ_LIST)

        self.__expect_tok((FTProto.RES_LIST,))

        list_len = self.fts.recv_int()

        for _ in range(list_len):
            path = self.fts.recv_rstring().decode()
            (hashd, is_dir, mtime) = self.fts.recv_struct('!32s?i')

            file_list.append(FileInfo(path=Path(path), file_hash=hashd, is_dir=is_dir, mtime=mtime))

        return file_list
