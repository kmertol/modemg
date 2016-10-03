#!/usr/bin/env python
# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file
import telitserial
import sys
import time

SLEEP_AFTER_RESET = 3

def reset(com_port):
	with telitserial.TelitSerial(com_port, verbose=True) as ser:
		return ser.telit_cmd('AT#ENHRST=1,0', 'OK', 2)

def after_reset(com_port):
	try:
		with telitserial.TelitSerial(com_port, verbose=True) as ser:
			return ser.telit_cmd('AT', 'OK')
	except telitserial.serial.SerialException:
		time.sleep(2)
		with telitserial.TelitSerial(com_port, verbose=True) as ser:
			return ser.telit_cmd('AT', 'OK')

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print(sys.argv[0], "com_port")
		sys.exit(-1)

	com_port = sys.argv[1]

	result = reset(com_port)
	if result:
		print("Sleeping after reset for {} seconds".format(SLEEP_AFTER_RESET), flush=True)
		time.sleep(SLEEP_AFTER_RESET)
		result = after_reset(com_port)

	sys.exit(0 if result else -1)
