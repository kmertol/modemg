# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file
import serial
import time

class TelitSerial(serial.Serial):
	def __init__(self, com_port='', verbose=False):
		serial.Serial.__init__(self, com_port, 115200, timeout=0)
		self.verbose = verbose
		self.init_time = time.time()

	def telit_write(self, data):
		if type(data) == str:
			data = bytearray(data, encoding='utf-8')

		if data[-1] != b'\r':
			data += b'\r'

		if self.verbose:
			print('{0:.3f} ----> Telit : {1}'.
			      format(time.time()-self.init_time, data, flush=True))
		return self.write(data)

	def telit_rsp(self, match, timeout=0.1, reject=None):
		if type(match) == str:
			match = bytes(match, encoding='utf-8')

		if type(reject) == str:
			reject = bytes(reject, encoding='utf-8')

		buf = bytearray(b'')
		timeout = int(timeout * 40)
		# At least one entry
		if timeout == 0:
			timeout = 1

		isfound = False
		for i in range(timeout):
			newbuf = self.read(256)
			if newbuf:
				buf += newbuf
				if match in buf:
					isfound = True
					break
				if reject and reject in buf:
					isfound = False
					break
			time.sleep(0.025)

		if self.verbose:
			print('{0:.3f} Telit ----> : {1}'.
			      format(time.time()-self.init_time, buf), flush=True)
		# 20ms min wait after receiving from telit until next transmission
		time.sleep(0.025)
		return isfound

	def telit_cmd(self, command, match, timeout=0.1, reject=None):
		self.telit_write(command)
		if self.telit_rsp(match, timeout, reject):
			return True
		else:
			print('Telit NoRsp:', command, flush=True)
			return False
