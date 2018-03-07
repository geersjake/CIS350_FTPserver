import socket
import struct
import random
import enum

class FTProto:
	# Ready to send data, followed by a ulong each of message
	# length and a uid sent with READY_RECV and ACKNOWLEDGE
	READY_SEND = b'S'

	# Ready for receive data, followed by a ulong each of
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

class FTSock:
	# Basis taken from python socket howto
	def __init__(self, sock=None):
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			# TODO: Remove this, it does stuff to make testing work easier
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		else:
			self.sock = sock

		random.seed()

	def conclient(self, host, port):
		self.sock.connect((host, port))

	def conserver(self, host, port):
		self.sock.bind(("", port))
		conn, addr = "", ""
		while (addr != host):
			self.sock.listen(1)
			conn, (addr, port) = self.sock.accept()

		self.sock = conn


	def connect(self, host, port):
		msg = ""
		try:
			self.conclient(host, port)
		except ConnectionRefusedError:

			try:
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
		chunks = []
		totalrecvd = 0
		while totalrecvd < num:
			chunk = self.sock.recv(min(num-totalrecvd, 2048))
			if chunk == b'':
				raise RuntimeError("Socket connection broken")
			chunks.append(chunk)
			totalrecvd = totalrecvd + len(chunk)
		return b''.join(chunks)

	def recvstruct(self, fmt):
		len = struct.calcsize(fmt)
		return struct.unpack(fmt, self.recvbytes(len))

	def sendbytes(self, str):
		num = len(str)
		totalsent = 0
		while totalsent < num:
			sent = self.sock.send(str[totalsent:])
			if sent == 0:
				raise RuntimeError("Socket connection broken")
			totalsent = totalsent + sent

	def recvmsg(self):
		cmd = self.recvbytes(1)

		if cmd != FTProto.READY_SEND:
			return -1
		
		mlen, muid = self.recvstruct("!II")
		resp = struct.pack("!II", mlen, muid)
		self.sendbytes(FTProto.READY_RECV)
		self.sendbytes(resp)

		cmd = self.recvbytes(1)

		if cmd != FTProto.DATA_SEND:
			return -2

		return self.recvbytes(mlen)


	def sendmsg(self, msg):
		msglen = len(msg)
		if msglen > (2**32):
			raise RuntimeError("Message too long")

		uid = random.randint(0, 2**32)

		header = struct.pack("!II", msglen, uid)
		self.sendbytes(FTProto.READY_SEND)
		self.sendbytes(header)

		resp = self.recvbytes(1)
		if resp == FTProto.READY_RECV:
			rlen, ruid = self.recvstruct("!II")
			if (rlen != msglen or ruid != uid):
				self.sendbytes(FTProto.ERR_CANCEL)
				return False, "Response mismatch"
			self.sendbytes(FTProto.DATA_SEND)
			self.sendbytes(msg)




