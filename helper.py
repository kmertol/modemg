# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file

import MOD
import md5

# I am used to these, but they are not defined in Python 1.x
True = 1
False = 0

class LoopTerminate: pass

def strstr(s, needle):
	if s.find(needle) == -1:
		return 0
	else:
		return 1

def safe_eval_string(s):
	try:
		if not ((s[0] == '"' and s[-1] == '"')
		    	or (s[0] == "'" and s[-1] == "'")):
		    return None
		s = eval(s, {}, {})
		if type(s) == type(''):
			return s
		else:
			return None
	except Exception:
		return None

class Config:
	serial_magic_keywords = ('{yy}', '{MM}', '{dd}', '{hh}', '{mm}', '{ss}')

	def __init__(self):
		def file_exists(file):
			try:
				f = open(file)
			except IOError:
				return False

			f.close()
			return True

		def read_file(file):
			try:
				f = open(file)
			except IOError:
				return ''

			s = f.read()
			f.close()
			return s

		def write_file(file, s):
			try:
				f = open(file, 'w')
			except IOError:
				return False

			f.write(s)
			f.close()
			return True

		def md5sum(s):
			return md5.new(s).digest()

		self._uptime = None
		self._downtime = None
		self.imei = None
		self.disconnection = 0

		self.load_config_file("default.conf")

		if 0 != self.load_config_file("user.conf"):
			# None or invalid user.conf
			if 0 == self.load_config_file("user.conf~"):
				# Valid user.conf backup, copy into user.conf
				conf = read_file("user.conf~")
				if conf:
					conf_md5 = md5sum(conf)
					if write_file("user.conf", conf):
						write_file(".user.conf.md5", conf_md5)
			return

		# Control for user.conf~ and create backup as necessary
		conf = read_file("user.conf")
		if not conf:
			return
		conf_md5 = md5sum(conf)
		conf_md5_cache = read_file(".user.conf.md5")

		if not file_exists("user.conf~") or conf_md5 != conf_md5_cache:
			if write_file("user.conf~", conf):
				write_file(".user.conf.md5", conf_md5)

	def init_at(self, at):
		self.at = at

	def push_config(self, key, val):
		if val == 'true':
			val = 1
		elif val == 'false':
			val = 0

		try:
			if key == "pdp_type":
				self.pdp_type = val
			elif key == "pdp_apn":
				self.pdp_apn = val
			elif key == "pdp_username":
				self.pdp_username = val
			elif key == "pdp_password":
				self.pdp_password = val
			elif key == "pdp_authentication_type":
				self.pdp_authentication_type = val
			elif key == "serial_baud":
				self.serial_baud = val
			elif key == "serial_param":
				self.serial_param = val
			elif key == "serial_clear_buffer_after_connect":
				self.serial_clear_buffer_after_connect = val
			elif key == "serial_clear_buffer_after_at_bridge":
				self.serial_clear_buffer_after_at_bridge = val
			elif key == "socket_keep_alive":
				self.socket_keep_alive = val
			elif key == "socket_inactivity_timeout":
				self.socket_inactivity_timeout = val
			elif key == "socket_connection_timeout":
				self.socket_connection_timeout = val
			elif key == "socket_tx_timeout":
				self.socket_tx_timeout = val
			elif key == "socket_packet_size":
				self.socket_packet_size = val
			elif key == "socket_flush_char":
				self.socket_flush_char = val
			elif key == "socket_connection_type":
				self.socket_flush_char = val
			elif key == "servers":
				valid = False
				for server in val.split(","):
					pac = server.strip().split(':')
					# Set to default tcp
					if len(pac) == 2:
						pac.append("tcp")

					if len(pac) == 3:
						# Don't change unless there are no syntax errors
						if pac[2] == "udp":
							pac[2] = '1'
						else:
							pac[2] = '0'

						if valid:
							self.servers.append(pac)
						else:
							valid = True
							self.servers = [pac]
			elif key == "low_power_mode":
				self.low_power_mode = int(val)
				if self.low_power_mode > 100:
					self.low_power_mode = 100
			elif key == "power_saving":
				self.power_saving = val
			elif key == "verbose_trace":
				self.verbose_trace = val
			elif key == "connection_message":
				if val:
					s = safe_eval_string(val)
					if s:
						self.connection_message = s
					else:
						print("[connection message] syntax error")
						return False
				else:
					self.connection_message = ''
			elif key == "cell_info_count":
				self.cell_info_count = int(val)
			elif key == "at_bridge_timeout":
				self.at_bridge_timeout = int(val)
			elif key == "servers_retry_wait":
				self.servers_retry_wait = int(val)
			elif key == "servers_retry_immediately":
				self.servers_retry_immediately = val
			elif key == "downtime_reset":
				self.downtime_reset = int(val) * 60
			elif key == "periodic_reset":
				self.periodic_reset = val
			elif key == "periodic_reset_renew_on_connect":
				self.periodic_reset_renew_on_connect = val
			elif key == "serial_magic":
				if val:
					s = safe_eval_string(val)
					if s:
						self.serial_magic = s
					else:
						return False
				else:
					self.serial_magic = ''
			else:
				return False

			return True

		except Exception:
			return False

	def push_config_line(self, s):
		s = s.split("=", 1)
		if len(s) != 2:
			return False

		key = s[0].strip()
		val = s[1].strip()

		self.push_config(key, val)

	def load_config_file(self, config_file):
		start = MOD.secCounter()
		print("Loading config file " + config_file + "...")
		try:
			f = open(config_file)
		except IOError:
			print(config_file + " not found")
			return -1

		s = f.read().rstrip()
		f.close()

		if not s.endswith("END"):
			print("Invalid config file, no END line")
			return -2

		lines = s.split('\n')

		for line in lines:
			if len(line) <= 2 or line[0] == '#' or line[0] == '[':
				continue

			self.push_config_line(line)

		print("Load time " + config_file + ": " + str(MOD.secCounter()-start))
		return 0

	def load_identification(self):
		# No need to read imei again
		if not self.imei:
			self.at.send("AT+CGSN\r")
			res = self.at.receive()
			if strstr(res, 'OK'):
				self.imei = res.replace('OK','').strip()
			else:
				# self.imei = ''
				print("Can't read IMEI")

		self.at.send("AT#CIMI\r")
		res = self.at.receive()
		if strstr(res, 'OK'):
			start = res.find(' ')
			end = res.find('\r', start)
			self.imsi = res[start:end]
		else:
			self.imsi = ''
			print("Can't read IMSI")

		self.at.send("AT+CCID\r")
		res = self.at.receive()
		if strstr(res, 'OK'):
			start = res.find(' ')
			end = res.find('\r', start)
			self.iccid = res[start:end]
		else:
			self.iccid = ''
			print("Can't read ICCID")

		self.at.send("AT+CNUM\r")
		res = self.at.receive()
		if strstr(res, 'OK'):
			start = res.find(',') + 2
			end = res.find(',', start)
			self.msisdn = res[start:end - 1]
		else:
			self.msisdn = ''
			print("Can't read MSISDN")

		self.at.send("AT+COPS?\r")
		res = self.at.receive()
		if strstr(res, 'OK'):
			start = res.find('"') + 1
			end = res.find('"', start)
			self.operator = res[start:end]
		else:
			self.operator = ''
			print("Cant read Operator")

		# print(self.imei, self.imsi, self.msisdn, self.iccid, self.operator)

	def increment_disconnection(self):
		self.disconnection =  self.disconnection + 1

	def set_session_uptime(self):
		self._session_uptime = MOD.secCounter()

	def get_session_uptime(self):
		return MOD.secCounter() - self._session_uptime

	def set_uptime(self):
		if not self._uptime:
			self._uptime = MOD.secCounter()
			self._session_uptime = self._uptime
			self._downtime = self._uptime

	def get_uptime(self):
		return MOD.secCounter() - self._uptime

	def clr_downtime(self):
		self._downtime = MOD.secCounter()

	def get_downtime(self):
		return MOD.secCounter() - self._downtime

	def is_downtime_timeout(self):
		if not self.downtime_reset or self._downtime is None:
			return False
		else:
			if self.get_downtime() > self.downtime_reset:
				return True
			else:
				return False

	def get_csq(self):
		self.at.send("AT+CSQ\r")
		res = self.at.receive()
		if not strstr(res, "OK"):
			return ''
		start = res.find(":") + 2
		return res[start: res.find(",", start)]

	def get_gdatavol(self, type="1"):
		''' type = "1": session,  "2": total '''
		self.at.send("AT#GDATAVOL=" + type + "\r")
		res = self.at.receive()
		if not strstr(res, "OK"):
			return ''
		start = res.find(',') + 1
		return "[%s]" % res[start: res.find('\r', start)]

	def get_cell_info(self, cell_count=1):
		if cell_count == 0 or cell_count > 7:
			return ''

		self.at.send('AT+COPS=3,2;+COPS?\r')

		res = self.at.receive()
		if not res:
			return ''

		start = res.find('"')
		start = start + 1
		end = res.find('"', start)
		res = res[start:end]
		mcc = str(int(res[0:3]))
		mnc = str(int(res[3:]))

		self.at.send("AT#MONI=7;#MONI\r")
		res = self.at.receive()

		lines = res.split('\r\n')
		if len(lines) < 9:
			return ''

		cells = []
		for line in lines[2: 2 + cell_count]:
			lac = int(line[17:21], 16)
			cid = int(line[24:28], 16)
			if cid == 0 and lac == 65535:
				continue
			rssi = int(line[38:42])
			cells.append('{"mcc":%s,"mnc":%s,"cid":%d,"lac":%d,"rssi":%d}' %
			             (mcc, mnc, cid, lac, rssi))

		if cells:
			return "[%s]" % ','.join(cells)
		else:
			return ''

	def get_connection_message(self):
		s = self.connection_message
		if s:
			s = s.replace("{imei}", self.imei)
			s = s.replace("{imsi}", self.imsi)
			s = s.replace("{msisdn}", self.msisdn)
			s = s.replace("{iccid}", self.iccid)
			s = s.replace("{operator}", self.operator)
			s = s.replace("{disconnection}", str(self.disconnection))

			if strstr(s, "{csq}"):
				s = s.replace("{csq}", self.get_csq())
			if strstr(s, "{downtime}"):
				s = s.replace("{downtime}", str(self.get_downtime()))
			if strstr(s, "{session_uptime}"):
				s = s.replace("{session_uptime}", str(self.get_session_uptime()))
			if strstr(s, "{power_uptime}"):
				s = s.replace("{power_uptime}", str(self.get_uptime()))
			if strstr(s, "{gdatavol_total}"):
				s = s.replace("{gdatavol_total}", self.get_gdatavol("2"))
			if strstr(s, "{gdatavol_session}"):
				s = s.replace("{gdatavol_session}", self.get_gdatavol("1"))
			if strstr(s,"{cell}"):
				s = s.replace("{cell}", self.get_cell_info(self.cell_info_count))
		return s

	def get_serial_magic(self):
		if not self.serial_magic:
			return None

		self.at.send("AT#CCLK?\r")
		res = self.at.receive()
		if not strstr(res, 'OK'):
			return None

		start = res.find('"')
		res = res[start + 1:]
		time = (res[0:2], res[3:5], res[6:8], res[9:11], res[12:14], res[15:17])

		s = self.serial_magic

		i = 0
		for key in self.serial_magic_keywords:
			s = s.replace(key, time[i])
			i = i + 1

		return s

class AT:
	def __init__(self, mdm, verbose=0):
		self.verbose = verbose
		self.mdm = mdm

	def send(self, s, timeout=0):
		if s[-1] != '\r':
			s = s + '\r'
		if self.verbose:
			print("----> Telit: " + s)
		self.mdm.send(s, timeout)

	def receive(self, timeout=10):
		s = self.mdm.receive(timeout)
		if s:
			s = s + self.mdm.receive(1)
		if self.verbose:
			print("Telit ---->: " + s)
		return s

	def rsp(self, match, timeout=10, reject=None):
		s = ''
		isfound = False
		if type('') == type(match):
			match = [match]
		if type('') == type(reject):
			reject = [reject]

		try:
			for i in range(0, timeout):
				buf = self.mdm.receive(1)
				if buf:
					s = s + buf
					for needle in match:
						if strstr(s, needle):
							isfound = True
							raise LoopTerminate
					if reject:
						for needle in reject:
							if strstr(s, needle):
								raise LoopTerminate
		except LoopTerminate:
			pass

		if self.verbose:
			print("Telit ---->: " + s)
		return isfound

	def cmd(self, s, match, timeout=10, reject=None):
		self.send(s)
		if self.rsp(match, timeout, reject):
			return True
		else:
			return False

	def escape(self):
		MOD.sleep(10)
		self.mdm.send('+++', 1)
		self.rsp('OK', 30)

	def clean(self):
		# For a faster clean, and also to clean the receive buffer
		if self.cmd('AT\r', 'OK', 2):
		 	return True
		if self.cmd('AT\r', 'OK', 2):
			return True
		else:
			self.escape()
			if self.cmd('AT\r', 'OK'):
				return True
			else:
				return False
