import socket
import struct
import random
import enum

class FTProto:
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
	DATA_SEND  = b'D'

# 	TODO: Error checking and handling, plus properly closing the sockets and timing out

# Basic network unit, used for connecting and transferring data over TCP
class FTSock:
	# Basis taken from python socket howto
	def __init__(self, sock=None):
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			# 	TODO: Remove this, it does stuff to make testing work easier
			# (And could cause problems)
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		else:
			self.sock = sock

		# Seed RNG so UIDs are actually "Random"
		random.seed()

	# Connect to host as if it were a server
	def conclient(self, host, port):
		self.sock.connect((host, port))

	# 	Connect to a host *acting as the server* (only accepts from the host)
	# Could be changed to accept all connections but I like the symmetry
	def conserver(self, host, port):
		self.sock.bind(("", port))
		conn, addr = "", ""

		# Reject connections until the host matches
		while (addr != host):
			self.sock.listen(1)
			conn, (addr, port) = self.sock.accept()

		self.sock = conn


	# 	Tries connecting as a client, and if there is no server
	# present, start a server for the other host to connect to
	# 	Returns a boolean for connection success, a string for 
	# telling which mode we are in, and either "Success" or a
	# more descriptive error string
	def connect(self, host, port):
		msg = ""
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

	# Returns a set number of bytes received
	def recvbytes(self, num):
		chunks = []
		totalrecvd = 0
		while totalrecvd < num:
			chunk = self.sock.recv(min(num-totalrecvd, 2048))
			if chunk == b'':
				raise RuntimeError("Socket connection broken")
			chunks.append(chunk)
			totalrecvd = totalrecvd + len(chunk)
		return b''.join(chunks)

	# Returns an unpacked struct recieved
	def recvstruct(self, fmt):
		len = struct.calcsize(fmt)
		return struct.unpack(fmt, self.recvbytes(len))

	# Sends *only* the bytes passed in (no header etc)
	def sendbytes(self, str):
		num = len(str)
		totalsent = 0
		while totalsent < num:
			sent = self.sock.send(str[totalsent:])
			if sent == 0:
				raise RuntimeError("Socket connection broken")
			totalsent = totalsent + sent

	# TODO: Rewrite these to use the original socket.{send,recv}msg()?

	# Receives a message, handling lengthy and transacty stuff
	def recvmsg(self):
		# 	Hopefully we can move the initial command handling to the main loop
		# at some point
		cmd = self.recvbytes(1)
		if cmd != FTProto.READY_SEND:
			return -1
		# i.e. ^ that stuff
		
		# length and uid are always sent after the READY_SEND
		mlen, muid = self.recvstruct("!II")

		# Repack and send response
		resp = struct.pack("!II", mlen, muid)
		self.sendbytes(FTProto.READY_RECV)
		self.sendbytes(resp)

		# Make sure they are sending the data :P
		cmd = self.recvbytes(1)
		if cmd != FTProto.DATA_SEND:
			return -2

		# Receive the data
		return self.recvbytes(mlen)

	# Sends a message, handling lengthy and transacty stuff
	def sendmsg(self, msg):

		msglen = len(msg)

		# Message length must fit in a ulong
		if msglen > (2**32):
			raise RuntimeError("Message too long")

		uid = random.randint(0, 2**32)

		# Send header to see if they are ready
		header = struct.pack("!II", msglen, uid)
		self.sendbytes(FTProto.READY_SEND)
		self.sendbytes(header)

		# Make sure they are ready
		resp = self.recvbytes(1)
		if resp == FTProto.READY_RECV:
			rlen, ruid = self.recvstruct("!II")
			if (rlen != msglen or ruid != uid):
				self.sendbytes(FTProto.ERR_CANCEL)
				return False, "Response mismatch"

			# Send the data
			self.sendbytes(FTProto.DATA_SEND)
			self.sendbytes(msg)




