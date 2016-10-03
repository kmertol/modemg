#!/usr/bin/env python
# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file
import socket
import serial
import sys
import random
import time
import tqdm

class SocketClosed(BaseException): pass

def wait_for_connection_message(conn):
	delta = time.time()
	print('Waiting for Connection message')
	while True:
		ch = conn.recv(1)
		if not ch:
			raise SocketClosed
		else:
			if ch == b'\n':
				print("Connection message delay: {} seconds".format(round(time.time() - delta, 1)))
				break

def pactest(com_port=None, listen_port=None, pac_len=1024, reconnection=0, baud_rate=115200):
	# Open Serial Port
	ser = serial.Serial(com_port, baud_rate, timeout=0)

	# Open Socket
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(("",listen_port))
		print('Socket Created')
	except socket.error:
		print("Failed to create socket")
		sys.exit(-2)

	s.listen()
	print('Socket Listening')

	packet_com = bytearray([random.randint(0,255) for x in range(pac_len)])
	packet_modem = bytearray([random.randint(0,255) for x in range(pac_len)])

	for i in range(1, reconnection + 2):
		try:
			conn, addr = s.accept()
			print('Client connected:', addr)

			wait_for_connection_message(conn)
			# print('1 sec delay after reception')
			# time.sleep(1)

			print('Sending Packet --> COM:', pac_len, 'bytes')
			ser.write(packet_com)
			delta = time.time()

			print('Receiving Packet --> MODEM ...')
			pbar = tqdm.tqdm(pac_len, unit='Bytes')
			data = b''
			while True:
				# +4 if there is more data in the buffer also error
				buf = conn.recv(pac_len + 4)
				if not buf:
					pbar.close()
					print('FAIL: Client closed connection')
					s.close()
					ser.close()
					sys.exit(-2)

				pbar.update(len(buf))
				data += buf
				if len(data) >= pac_len:
					break
			pbar.close()


			if data != packet_com:
				print('FAIL: COM --> MODEM')
				# print('Received:', len(data), 'bytes')
				s.close()
				ser.close()
				sys.exit(-2)
			else:
				delta = int((time.time() - delta) * 1000)
				print('SUCCESS: COM --> MODEM' + ':: Delta Time(ms): ' , delta)

			# Devour telit print, error messages on the com port
			ser.reset_input_buffer()

			print('Sending Packet MODEM:', pac_len, 'bytes')
			sent_len = conn.send(packet_modem)
			delta = time.time()
			if sent_len != pac_len:
				print('Failed sending data')
				s.close()
				ser.close()
				sys.exit(-2)

			print('Receiving Packet --> COM ...')
			data = b''
			pbar = tqdm.tqdm(pac_len, unit='Bytes')
			while True:
				# +4 if there is more data in the buffer also error
				buf = ser.read(pac_len + 4)
				if buf:
					pbar.update(len(buf))
					data += buf
					if len(data) >= pac_len:
						break
					time.sleep(0.01)

			pbar.close()

			if data != packet_modem:
				print('FAIL: MODEM --> COM')
				# print('Received:', len(data), 'bytes')
				s.close()
				ser.close()
				sys.exit(-2)
			else:
				delta = int((time.time() - delta) * 1000)
				print('SUCCESS: MODEM --> COM' + ':: Delta Time(ms): ' , delta)


			print("SUCCESS #{}: Closing connection ".format(i), addr[0])
			conn.close()

		except KeyboardInterrupt:
			print("Interrupted")
			s.close()
			conn.close()
			ser.close()
			sys.exit(-3)


if __name__ == '__main__':
	usage = "{} com_port tcp_port [packet_length=1024] [reconnection=0] [baud_rate=115200]".format(__file__)

	if len(sys.argv) < 3 or len(sys.argv) > 6:
		print(usage)
		sys.exit(-1)
	else:
		args = sys.argv[1:]
		com_port = sys.argv[1]
		args = [int(arg) for arg in sys.argv[2:]]
		pactest(com_port, *args)
		sys.exit(0)
