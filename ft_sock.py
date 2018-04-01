"""Class to handle basic connection mechanics. Used by ft_conn to send and
data from the other host after the connection is established.
:Authors:
    Colton Bates

:Version 0.5
"""

import socket
import struct # For networky data packing
import queue  # For the timeout stack
import ssl

class FTProto:
    """Internally used to define control tokens for data transmission.
    Technically this could be an enum or a struct or something, but this
    is slightly easier and works best.
    """

    # 	Ready to send data, followed by a ulong each of message
    # length and a uid sent with READY_RECV and ACKNOWLEDGE
    READY_SEND = b'S'

    # 	Ready for receive data, followed by a ulong each of
    # message length and uid (for confirmation)
    READY_RECV = b'R'

    # An error occured, resend last message (including command)
    ERR_RESEND = b'E'

    # An error occured, cancel the current transaction (usually restarted)
    ERR_CANCEL = b'C'

    # Sent to request an ACK from the destination of data
    # followed by uid
    REQUEST_AK = b'K'

    # Sent after a message is successful, or it is requested
    # followed by uid
    ACKNOWLEDG = b'A'

    # Sent preceding actual data
    DATA_SEND = b'D'

class UnexpectedValueError(RuntimeError):
    """Raised when we receive something we did not expect according to the
    protocol specifications.
    """

    def __init__(self, state, value):
        """:param state: Identifies the state we were in (and hence what we were
        expecting).
        :type state: string
        :param value: The data we got instead of what we were expecting.
        :type value: string
        """
        super().__init__()
        self.state = state
        self.value = value

    def __repr__(self):
        """:return: The human-readable construction of the error.
        :rtype: string
        """
        return "UnexpectedValueError('" + self.state + "', '" + self.value + "'')"

    def __str__(self):
        """:return: The string representation of the error (as would be printed,
        etc.).
        :rtype: string
        """
        return "in " + self.state + ", but got " + self.value

class BrokenSocketError(RuntimeError):
    """Raised when the socket connection is broken unexpectedly.
    """

    def __str__(self):
        """:return: The string representation of the error (as would be printed,
        etc.).
        :rtype: string
        """
        return "Socket broken unexpectedly"

# Basic network unit, used for connecting and transferring data over TCP
class FTSock:
    """Wraps the default socket object to allow pseudo-symmetric connection and
    arbitrary message sending."""


    def __init__(self, sock=None):
        """Initializes the ft_sock object
        :param sock: Socket object to use. If not provided (or None), we
        generate a new one.
        :type sock: socket.socket()
        """
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # 	TODO: Remove this, it does stuff to make testing work easier
            # (And could cause problems)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            self.sock = sock

        # Initialize timeout stack
        self.tostack = queue.Queue()

    # 	These three functions allow us to quickly and easily switch between
    # timeouts
    def topush(self, val):
        """Push a value to the timeout stack (basically set a timeout but keep
        track of old values so they can be restored afterwards).
        :param val: timeout value to set, in seconds.
        :type val: number
        """
        self.tostack.put(self.sock.gettimeout())
        self.sock.settimeout(val)

    def topop(self):
        """Pop a value from the timeout stack (basically restore a timeout to
        before the last call to topush()). If the timeout stack is empty (i.e.
        there were no previous pushes that weren't popped), default to blocking
        mode.
        :return: The old value for timeout, in seconds.
        :rtype: number
        """
        oldtimeout = self.sock.gettimeout()

        # If the queue is empty, default to None (blocking mode) (shouldn't happen)
        newtimeout = None if self.tostack.empty() else self.tostack.get()

        self.sock.settimeout(newtimeout)
        return oldtimeout

    def settimeout(self, val):
        """Set the timeout, without messing with the stack (and by doing so, messing
        up the stack).
        :param val: timeout value to set, in seconds.
        :type val: number:
        """
        self.sock.settimeout(val)

    def conclient(self, host, port):
        """Connect to host as if we are the client and they are the server.
        :param host: Host to connect to (usually an IP).
        :type host: string
        :param port: Port to connect to on host.
        :type port: number
        """
        self.sock.connect((host, port))

    def conserver(self, host, port):
        """ Connect to host as if we are the server and they are the client (i.e.
        listen for connections from this host).
        :param host: Host to accept connections from (usually an IP).
        :type host: string
        :param port: Port to listen on.
        :type port: number
        """
        self.sock.bind(("", port))
        conn, addr = "", ""

        # Reject connections until the host matches (within 5m)
        self.topush(480)
        while addr != host:
            self.sock.listen(1)
            conn, (addr, port) = self.sock.accept()
        self.topop()

        self.sock = conn

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
            self.conclient(host, port)

        # This is the error that we will get if there is no server
        # 	running on the other host
        except ConnectionRefusedError:

            try: # Connecting as server <- client
                self.conserver(host, port)
            except socket.error as smsg:
                print("s", smsg)
                return False, "Server", smsg

            return True, "Server", "Success"

        except socket.error as cmsg:
            print("c", cmsg)
            return False, "Client", cmsg

        return True, "Client", "Success"

    def recvbytes(self, num):
        """Receives a known number of bytes from the other host.
        :param num: The number of bytes to receive.
        :type num: number
        :return: The bytes received.
        :rtype: raw string

        :raises BrokenSocketError: when the socket is broken before
        we recieve the specified number of bytes.
        """

        chunks = []
        totalrecvd = 0
        while totalrecvd < num:
            chunk = self.sock.recv(min(num-totalrecvd, 2048))
            if chunk == b'':
                raise BrokenSocketError()
            chunks.append(chunk)
            totalrecvd = totalrecvd + len(chunk)
        return b''.join(chunks)

    def recvstruct(self, fmt):
        """Receives and unpacks a struct.
        :param fmt: A struct format string that describes what to receive.
        :type fmt: string
        :return: The unpacked struct (usually a tuple/list).
        :rtype: Whatever struct.unpack() returns for the format provided
        (usually an indexable tuple/list).
        """

        slen = struct.calcsize(fmt)
        return struct.unpack(fmt, self.recvbytes(slen))

    def sendbytes(self, bstr):
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
