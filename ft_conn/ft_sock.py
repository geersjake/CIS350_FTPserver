"""Class to handle basic connection mechanics. Used by ft_conn to send and
data from the other host after the connection is established.
"""

import socket
import struct            # For networky data packing
from queue import Queue  # For the timeout stack
from .ft_error import BrokenSocketError

# Basic network unit, used for connecting and transferring data over TCP
class FTSock:
    """Wraps the default socket object to allow pseudo-symmetric connection and
    arbitrary message sending."""


    def __init__(self, test=False, sock=None):
        """Initializes the ft_sock object

        :param test: If True, allows sockets to be reused quickly, which
            makes testing much faster
        :type test: boolean

        :param sock: Socket object to use. If not provided (or None), we
        generate a new one.
        :type sock: socket.socket()
        """

        self.sock = None
        # Initialize timeout stack
        self.timeout_stack = []

    # 	These three functions allow us to quickly and easily switch between
    # timeouts
    def timeout_push(self, val):
        """Push a value to the timeout stack (basically set a timeout but keep
        track of old values so they can be restored afterwards).

        :param val: timeout value to set, in seconds.
        :type val: number
        """

        self.timeout_stack.append(val)
        if self.sock:
            self.sock.settimeout(self.timeout_get())

    def timeout_pop(self):
        """Pop a value from the timeout stack (basically restore a timeout to
        before the last call to timeout_push()). If the timeout stack is empty (i.e.
        there were no previous pushes that weren't popped), default to blocking
        mode.

        :return: The old value for timeout, in seconds.
        :rtype: number
        """

        last = self.timeout_stack.pop()
        if self.sock:
            self.sock.settimeout(self.timeout_get())
        return last

    def timeout_get(self):
        if len(self.timeout_stack) >= 1:
            return self.timeout_stack[-1]
        else:
            return None

    def set_socket(self, sock):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError as ex:
                print('OSError while shutting down socket:', ex)
            self.sock.close()
            self.sock = None
        self.sock = sock
        if self.sock:
            self.sock.settimeout(self.timeout_get())

    def __connect_client(self, host, port):
        """Connect to host as if we are the client and they are the server.

        :param host: Host to connect to (usually an IP).
        :type host: string

        :param port: Port to connect to on host.
        :type port: number
        """

        self.set_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

        try:
            self.sock.connect((host, port))
        except Exception as ex:
            self.set_socket(None)
            raise ex

    def __connect_server(self, host, port):
        """ Connect to host as if we are the server and they are the client (i.e.
        listen for connections from this host).

        :param host: Host to accept connections from (usually an IP).
        :type host: string

        :param port: Port to listen on.
        :type port: number
        """
        self.set_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

        try:
            self.sock.bind(("", port))
            conn, addr = "", ""

            # Reject connections until the host matches (within 5m)
            self.timeout_push(300)
            while True:
                self.sock.listen(1)
                conn, (addr, port) = self.sock.accept()

                if addr == host:
                    break
                else:
                    print("Closing for some reason")
                    self.set_socket(None)

            self.timeout_pop()

            self.sock = conn
        except Exception as ex:
            self.set_socket(None)
            raise ex

    def connect(self, host, port):
        """Starts a pseudo-symmetric connection by trying to connect to
        the host as a client, and if that doesn't work (i.e. there is
        no server running on the other host), start listening as a server.

        :param host: The host to connect to (usually an IP).
        :type host: string

        :param port: The port to use for the server's connection.
        :type port: string

        :return: A boolean representing the success (True
            for success, False for failure), a string representing the mode
            of connection we are in ("Client" or "Server"), and another string
            which is either "Success", or a description of the error that
            occurred.

        :rtype: boolean, string, string
        """

        try: # Connecting as client -> server
            self.__connect_client(host, port)

        # This is the error that we will get if there is no server
        # 	running on the other host
        except ConnectionRefusedError:
            self.__connect_server(host, port)
            return True, "Server", "Success"

        return True, "Client", "Success"

    def recv_bytes(self, num):
        """Receives a known number of bytes from the other host.

        :param num: The number of bytes to receive.
        :type num: number

        :return: The bytes received.
        :rtype: raw string

        :raises BrokenSocketError: when the socket is broken before
            we recieve the specified number of bytes.
        """

        if not self.sock:
            return None

        if num == 0:
            return b''

        chunks = []
        totalrecvd = 0
        while totalrecvd < num:
            chunk = self.sock.recv(min(num-totalrecvd, 2048))
            if chunk == b'':
                raise BrokenSocketError()
            chunks.append(chunk)
            totalrecvd = totalrecvd + len(chunk)
        return b''.join(chunks)

    def recv_struct(self, fmt):
        """Receives and unpacks a struct.

        :param fmt: A struct format string that describes what to receive.
        :type fmt: string

        :return: The unpacked struct (usually a tuple/list).

        :rtype: Whatever struct.unpack() returns for the format provided
            (usually an indexable tuple/list).
        """

        slen = struct.calcsize(fmt)
        return struct.unpack(fmt, self.recv_bytes(slen))

    def recv_rstring(self):
        """Receives a string from the network sensibly (fixed-length).

        :return: The string received.
        :rtype: string
        """

        length = self.recv_struct('!i')[0]
        rstr = self.recv_struct('!{}s'.format(length))[0]
        return rstr

    def recv_int(self):
        """Receives an integer from the network.

        :return: The integer received.
        :rtype: integer
        """

        return self.recv_struct('!i')[0]

    def send_bytes(self, bstr):
        """Send raw bytes over the connection.

        :param bstr: A raw string of data to send.
        :type bstr: raw string

        :raises BrokenSocketError: when the socket is broken before we
            send all of the bytes passed.
        """
        num = len(bstr)
        totalsent = 0
        while totalsent < num:
            sent = self.sock.send(bstr[totalsent:])
            if sent == 0:
                raise BrokenSocketError()
            totalsent = totalsent + sent

    def send_tok(self, token):
        """Sends a token by sending its raw schar equivalent.

        :param token: The token to send.
        :type token: FTProto
        """

        self.send_bytes(token)

    def send_struct(self, fmt, *data):
        """Packs and sends data over the network as a struct.

        :param fmt: A struct format string describing the data packing.
        :type fmt: string

        :param data: Rest of data, as passed to struct.pack().
        :type data: whatever the structure describes
        """

        self.send_bytes(struct.pack(fmt, *data))

    def send_rstring(self, rstr):
        """Packs and sends a raw string sensibly.

        :param rstr: The raw string to send.
        :type rstr: raw string
        """

        self.send_struct('!i{}s'.format(len(rstr)), len(rstr), rstr)

    def send_int(self, num):
        """Sends an integer over the network.

        :param num: The integer to send.
        :type num: integer
        """

        self.send_struct('!i', num)
