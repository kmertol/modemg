# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file

import sys
import SER
import GPIO
import MDM
import MDM2
import MOD
from helper import *

############### Exceptions ###############
class NoCarrier: pass
class NoRsp: pass
############### Timeouts ###############
TIMEOUT_CPIN_SEC = 6
TIMEOUT_CGREG = 12
# The watchdog timeout value is a little higher than the maximum allowed 140s
# (120s connect + 20s Dns resolution) for the socket opening timeout,
# so we can use this timeout without going into the hassle of changing
# it across different places
WATCHDOG_TIMEOUT = 145
############### Initialization ###############
print("---------- Initializing ----------")
# Status LED, This is the auto mode
sled_set_auto = lambda : GPIO.setSLED(2, 10 , 10)
# Status LED, 100 ms on , 1400ms off
sled_set_connected = lambda : GPIO.setSLED(3, 1, 14)
# We are enabling the led at the beginning, so that the user knows that the
# device has started working
sled_set_auto()

config = Config()
SER.set_speed(config.serial_baud, config.serial_param)

at = AT(MDM, config.verbose_trace)
at2 = AT(MDM2, config.verbose_trace)
config.init_at(at2)
#####################################

def quit(s):
	print('Quitting:: %s' % s)
	sys.exit(-1)

NO_CARRIER = "\r\nNO CARRIER\r\n"

def serial_clear_buffer():
	# Waiting for a 100ms quiet time (max 1s), so that we could have an intact data
	for i in range(0, 10):
		s = SER.receive(1)
		if not s:
			break

class Bridge:
	def __init__(self, get_conn_msg=lambda:'', clr_serial_buf=True, clr_at_buf=True,
	              at_bridge_timeout=0, low_power_mode=1, power_saving=False):
		self.get_conn_msg = get_conn_msg
		self.clr_serial_buf = clr_serial_buf
		self.clr_at_buf = clr_at_buf
		self.at_bridge_timeout = at_bridge_timeout
		if power_saving:
			self.sleep_time = (low_power_mode + 9) / 10
			self.enter_sleep = self.powersaving_sleep
		else:
			self.sleep_time = low_power_mode
			self.enter_sleep = self.mod_sleep

	def mod_sleep(self):
		MOD.sleep(self.sleep_time)

	def powersaving_sleep(self):
		MOD.powerSaving(self.sleep_time)

	def at_bridge(self):
		timeout_exit = MOD.secCounter() + self.at_bridge_timeout
		while MDM.getDCD():
			# NET to AT
			s = MDM.receive(1)
			if s:
				if s.endswith(NO_CARRIER):
					at2.clean()
					raise NoCarrier
				if s == "+++":
					MDM.send('OK\r\n', 1)
					# Clean if what the user left is messy
					at2.clean()
					return
				MDM2.send(s, 1)
				timeout_exit = MOD.secCounter() + self.at_bridge_timeout

			s = MDM2.receive(1)
			if s:
				MDM.send(s, 1)

			MOD.watchdogReset()

			if self.at_bridge_timeout and MOD.secCounter() > timeout_exit:
				MDM.read()
				at2.clean()
				return

		MDM.read()
		at2.clean()
		raise NoCarrier

	def serial_bridge(self):
		s = self.get_conn_msg()
		if self.clr_serial_buf:
			serial_clear_buffer()
		if s:
			MDM.send(s, 10)

		while MDM.getDCD():
			# From NET to Serial
			for i in range(0, 8):
				s = MDM.read()
				if s:
					if s.endswith(NO_CARRIER):
						# the previous data can be important
						SER.send(s[:-len(NO_CARRIER)])
						raise NoCarrier
					if s == "+++":
						MDM.send('OK\r\n', 10)
						print("Entering AT bridge")
						self.at_bridge()
						if self.clr_at_buf:
							serial_clear_buffer()
						print("Exiting AT bridge")
					else:
						SER.send(s)
				else:
					break
			# From Serial to NET
			s = SER.read()
			if s:
				MDM.send(s, 10)
			# A bit of sleep
			self.enter_sleep()
			MOD.watchdogReset()

		# Catch the NOCARRIER, don't want to send it back to serial
		s = MDM.receive(1)
		if s.endswith(NO_CARRIER):
			# the previous data can be important
			SER.send(s[:-len(NO_CARRIER)])

		raise NoCarrier

class Sleep:
	def __init__(self, sec=0, power_saving=False):
		self.sec = sec
		if power_saving:
			self.sleep = self.powersaving_sleep
		else:
			self.sleep = self.mod_sleep

	def mod_sleep(self):
		MOD.powerSaving(10 * self.sec)

	def powersaving_sleep(self):
		entry = MOD.secCounter()
		rem = self.sec
		while 1:
			MOD.powerSaving(rem)
			if MOD.powerSavingExitCause():
				break
			elapsed = MOD.secCounter() - entry
			entry = elapsed
			if elapsed < 0:
				break
			rem = rem - elapsed
			if rem <= 0:
				break

	def enter(self):
		if not self.sec:
			return

		print("Sleeping for %d seconds, before retrying servers..." % self.sec)

		if self.sec > WATCHDOG_TIMEOUT - 5:
			MOD.watchdogEnable(self.sec + 5)
		else:
			MOD.watchdogReset()

		self.sleep()

		MOD.watchdogEnable(WATCHDOG_TIMEOUT)

def at_cleaner():
	if not at.clean():
		quit("AT interface failure")

def run():
	serial_clear_buffer()

	MOD.watchdogEnable(WATCHDOG_TIMEOUT)
	# Can enter power saving, if we are clearing serial buffer
	if config.serial_clear_buffer_after_connect or config.power_saving:
		power_saving = True
	else:
		power_saving = False
	sleep = Sleep(config.servers_retry_wait, power_saving)
	# Configure bridge parameters
	bridge = Bridge(config.get_connection_message, config.serial_clear_buffer_after_connect,
		config.serial_clear_buffer_after_at_bridge, config.at_bridge_timeout,
		config.low_power_mode, config.power_saving)
	# First configure NVM and one time configured data
	if config.periodic_reset != '0':
		at.cmd("AT#ENHRST=2,%s\r" % config.periodic_reset, "OK")
	else:
		at.cmd("AT#ENHRST=0\r", "OK")

	############### Context Configuration ###############
	print('Configuring --> Context')
	s = 'AT+CGDCONT=1,"%s","%s"\r' % (config.pdp_type, config.pdp_apn)
	if not at.cmd(s, 'OK'):
		quit('Failed context')

	############### Socket Configuration ###############
	print('Configuring --> Socket')

	s = 'AT#SCFG=1,1,%s,%s,%s,%s\r' % \
		(config.socket_packet_size, config.socket_inactivity_timeout,
		config.socket_connection_timeout, config.socket_tx_timeout)
	if not at.cmd(s, 'OK'):
		quit('Socket configuration failed')

	if not at.cmd('AT#SCFGEXT=1,0,0,%s\r' % config.socket_keep_alive, 'OK'):
		quit('Socket configuration failed')

	############### Skip Esc ###############
	at.cmd("AT#SKIPESC=1\r", 'OK')

	############### Flush Char ###############
	if config.socket_flush_char:
		at.cmd("AT#PADCMD=1", "OK")
		at.cmd("AT#PADFWD=%s\r" % config.socket_flush_char, "OK")

	############### Authentication Type ###############
	if config.pdp_authentication_type:
		if not at.cmd("AT#SGACTAUTH=%s" % config.pdp_authentication_type, "OK"):
			quit("Can't set authentication type")

	############### MAIN LOOP ###############
	while 1:
		try:
			at_cleaner()

			if config.is_downtime_timeout():
				quit("Downtime timeout")
			MOD.watchdogReset()

			############ SIM ###############
			print("Controlling --> SIM")

			timeout = MOD.secCounter() + TIMEOUT_CPIN_SEC
			while 1:
				at.send('AT+CPIN?\r')
				res = at.receive()
				if strstr(res, 'READY'):
					break
				elif strstr(res,'SIM PIN'):
					if not config.sim_pin:
						quit("No SIM PIN supplied")
					if not at.cmd('AT+CPIN=' + config.sim_pin, 'OK'):
						quit("SIM PIN rejected")
				else:
					if MOD.secCounter() > timeout:
						print("Forcing Sim Detection")
						at.send('AT#SIMDET=0\r')
						at.receive()
						at.send('AT#SIMDET=1\r')
						at.receive()
						# Just to make it start from beginning of the main loop
						raise NoRsp
					else:
						MOD.sleep(10)

			############### Load Identification ###############
			# IMEI and SIM data
			config.load_identification()

			########### Network available ? ############
			print("Controlling --> Network")
			timeout = MOD.secCounter() + TIMEOUT_CGREG
			online = False
			while MOD.secCounter() < timeout:
				if at.cmd("AT+CGREG?\r", 'CGREG: 0,1'):
					online = True
					break
				MOD.sleep(5)

			if not online:
				raise NoRsp

			# Setting uptime with MOD.secCounter() only valid when gsm network found
			config.set_uptime()
			s = config.get_serial_magic()
			if s:
				SER.send(s)
			############### Server Connect Loop ###############
			while 1:
				at_cleaner()
				MOD.watchdogReset()
				############### Get IP ###############
				print('Controlling --> IP')
				at.send("AT#SGACT?\r")
				res = at.receive()
				if not strstr(res, "#SGACT: 1,1"):
					if strstr(res, "ERROR"):
						print("GSM Network down, restarting process")
						break
					if not at.cmd("AT#SGACT=1,1,%s,%s\r" %
					            (config.pdp_username, config.pdp_password), ['#SGACT', '+IP:'], 300):
						print("Can't get IP, restarting process")
						break

					config.set_session_uptime()

				# Make sure the socket is closed
				if not at.cmd('AT#SH=1\r', 'OK', 40, 'ERROR'):
					break

				############### Connect to Server ###############
				try:
					n = 1
					for server in config.servers:
						MOD.watchdogReset()
						if server is not None:
							print("Trying --> Server #" + str(n))
							s = 'AT#SD=1,%s,%s,"%s"\r' % (server[2], server[1], server[0])
							# 20 seconds DNS resolution, and 1 sec extra
							if at.cmd(s, 'CONNECT', int(config.socket_connection_timeout) + 210, 'ERROR'):
								sled_set_connected()
								print('Connected')

								if config.periodic_reset_renew_on_connect and config.periodic_reset != '0':
									at2.cmd("AT#ENHRST=1,%s\r" % config.periodic_reset, "OK")

								bridge.serial_bridge()
						n = n + 1

					if config.is_downtime_timeout():
						quit("Downtime timeout")
					sleep.enter()

				except NoCarrier:
					sled_set_auto()
					print("Disconnected: attempting reconnection...")
					config.increment_disconnection()
					config.clr_downtime()
					# If not responding still open, then
					at_cleaner()
					if not config.servers_retry_immediately:
						sleep.enter()

		except NoRsp:
			pass
