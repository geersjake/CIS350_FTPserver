"""Class to handle transfer protocol and actual data transfer. Uses
ft_sock to provide network functionality.
:Authors:
    Colton Bates

:Version 0.5:
"""

import enum
from socket import timeout
from ft_sock import FTSock
from ft_error import UnexpectedValueError
from file_info import FileInfo

class FTProto(enum.Enum):
    """Internally used to define control tokens for data transmission.
    """

    # Used to request the remote filelist.
    REQ_LIST = b'l'

    # Used to request a file. Following is a string of the file name/path
    REQ_FILE = b'f'

    # Used to represent a lack of requests and invalid tokens, respectively.
    REQ_NONE = None
    TINVALID = None

    # Used to send the filelist. Following is a '!i' representing the
    # number of entries, and then each entry is sent as a string (path),
    # '!32s?i' (hash digest, is_dir, and mtime int).
    RES_LIST = b'L'

    # Used to send the file. Following is a raw string of the contents of the file
    RES_FILE = b'F'

class FTConn:
    """Provides useful network functionality to be called by the UI.
    """

    def __init__(self):
        self.fts = FTSock()

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

        _, _, status = self.fts.connect(host, port)
        return status

    def check_for_request(self):
        """Checks the network buffer to see if there are any requests
        we need to respond to.
        :return: FTProto.REQ_LIST, FTProto.REQ_FILE, or FTProto.REQ_NONE.
        If FTProto.REQ_FILE, also the filename requested, otherwise None.
        :rtype: FTProto, string

        :raises UnexpectedValueError: when we receive an invalid request.
        """
        self.fts.topush(0.1)

        try:
            reqr = self.fts.recvbytes(1)
        except timeout:
            reqr = None
        finally:
            self.fts.topop()

        req = self.__gtv(reqr)
        fname = None

        if req not in (FTProto.REQ_FILE, FTProto.REQ_LIST, FTProto.REQ_NONE):
            raise UnexpectedValueError('Request', reqr.decode())

        if req == FTProto.REQ_FILE:
            fname = self.fts.recvrstring().decode()

        return req, fname

    def send_file(self, file_data):
        """Sends file contents to other host.
        :param file_data: The file contents.
        :type file_data: raw string
        """
        self.fts.sendtok(FTProto.RES_FILE)
        self.fts.sendrstring(file_data)

    def send_file_list(self, file_list):
        """Sends the file list after a request.
        :param file_list: The file list to send (should be recently
        updated).
        :type file_list: list of FileInfo
        """

        self.fts.sendtok(FTProto.RES_LIST)

        list_length = len(file_list)
        self.fts.sendstruct('!i', list_length)

        for file_info in file_list:
            self.fts.sendrstring(str(file_info.path).encode())
            self.fts.sendstruct('!32s?i', file_info.hash.digest(),
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

        self.fts.sendtok(FTProto.REQ_FILE)
        self.fts.sendrstring(filename.encode())

        tokr = self.fts.recvbytes(1)
        tok = self.__gtv(tokr)

        if tok != FTProto.RES_FILE:
            raise UnexpectedValueError('File response', tokr.decode())

        return self.fts.recvrstring()

    def request_file_list(self):
        """Requests and receives a file list ffrom the other host.
        :return: A list containing all of the file information requested.
        :rtype: list of FileInfo (sort of, ???)

        :raises UnexpectedValueError: when the other host does
        not rspond to our request properly.
        """

        file_list = []

        self.fts.sendtok(FTProto.REQ_LIST)

        tokr = self.fts.recvbytes(1)
        tok = self.__gtv(tokr)

        if tok != FTProto.RES_LIST:
            raise UnexpectedValueError('File list response', tokr.decode())

        list_len = self.fts.recvstruct('!i')[0]

        for _ in range(list_len):
            path = self.fts.recvrstring().decode()
            (hashd, is_dir, mtime) = self.fts.recvstruct('!32s?i')

            # TODO: Make this a real FileInfo? It has a hash digest where the hash should be.

            file_list.append(FileInfo(path=path, file_hash=hashd, is_dir=is_dir, mtime=mtime))

        return file_list
