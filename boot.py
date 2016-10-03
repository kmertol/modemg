# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file

# Uncaught exceptions will end the current script, only way is to
# send AT#EXECSCR or reset the module to have it run again. We don't
# want it, so in here we are catching all exceptions and causing a
# reset of the module with a watchdog timeout.

import MOD
MOD.watchdogEnable(60)

import sys
import SER

TRACE_ON_SER = 0

def route_trace_to_ser():
	class SER_stdout:
		def write(self, s):
			SER.send(s)

	SER.set_speed("115200","8N1")
	sys.stdout = SER_stdout()
	sys.stderr = sys.stdout

def print_traceback():
	def tb_lineno(tb):
		c = tb.tb_frame.f_code
		if not hasattr(c, 'co_lnotab'):
			return tb.tb_lineno

		tab = c.co_lnotab
		line = c.co_firstlineno
		stopat = tb.tb_lasti
		addr = 0
		for i in range(0, len(tab), 2):
			addr = addr + ord(tab[i])
			if addr > stopat:
				break
			line = line + ord(tab[i+1])
		return line

	type, value, tb = sys.exc_info()
	print("Traceback (most recent call last):")
	while tb is not None :
		print('  File "%s", line %d, in %s' %
			(tb.tb_frame.f_code.co_filename, tb_lineno(tb),
			tb.tb_frame.f_code.co_name))
		tb = tb.tb_next
	print("%s: %s" % (type, value))

def reset():
	MOD.watchdogEnable(1)
	MOD.sleep(300)
	sys.exit(-1)

try:
	try:
		if TRACE_ON_SER:
			route_trace_to_ser()

		import modemg
		modemg.run()
	except:
		print_traceback()
finally:
	reset()
