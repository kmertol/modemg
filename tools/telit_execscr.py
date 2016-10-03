#!/usr/bin/env python
# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file
import telitserial
import sys

def execscr(com_port):
	with telitserial.TelitSerial(com_port, verbose=True) as ser:
		return ser.telit_cmd('AT#EXECSCR', 'OK', 1)

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print(sys.argv[0], "com_port")
		sys.exit(-1)

	com_port = sys.argv[1]
	sys.exit(0 if execscr(com_port) else -1)
