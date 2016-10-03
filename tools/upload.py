#!/usr/bin/env python
# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file
import sys
import os
import time
import tqdm
import telitserial

TELIT_WRITE_BUF_SIZE = 4000
TELIT_WRITE_BUF_DELAY = 1

def upload(files, com_port='', script_mode='', verbose=False, secure=False, verify=False):
	""" script_mode = ["run", "enable"] """
	# First file is the main script
	scriptname = os.path.basename(files[0])
	scriptext = os.path.splitext(scriptname)[1]

	with telitserial.TelitSerial(com_port, verbose) as ser:
		# Just a wake up call
		ser.telit_cmd('AT','OK', 0.5)

		if not ser.telit_cmd('ATE0', 'OK', 0.5):
			return -1

		if script_mode:
			if scriptext == '.pyo' or scriptext == '.pyc':
				if not ser.telit_cmd('AT#STARTMODESCR=1,10', 'OK', 2):
					return -1
			else:
				print("WARNING: Not setting Start Mode, extension is '{}': not a compiled script".format(scriptext))

		# Doesn't make much of a difference
		# if not ser.telit_cmd('AT#CPUMODE=7', 'OK', 0.5):
		# 	return -1

		for file in files:
			filesize = os.path.getsize(file)
			filename = os.path.basename(file)
			ext = os.path.splitext(filename)[1]

			if ext and secure and '.py' in ext:
				knowhow = '1'
			else:
				knowhow = '0'

			with open(file, 'rb') as f:
				filedata = f.read()

			if not ser.telit_cmd('AT#WSCRIPT="{0}",{1},{2}'.format(filename, filesize, knowhow), '>>>', 3, 'ERROR'):
				return -1

			print('Uploading {0} {1} Bytes ...'.format(filename, filesize))
			pbar = tqdm.tqdm(filesize, unit='Bytes')
			remaining = filesize
			written = 0
			while remaining:
				if remaining > TELIT_WRITE_BUF_SIZE:
					length = TELIT_WRITE_BUF_SIZE
				else:
					length = remaining

				ser.write(filedata[written:written+length])
				written += length
				remaining -= length
				pbar.update(length)
				if not remaining:
					break

				wait = (written // 4000) * TELIT_WRITE_BUF_DELAY * (TELIT_WRITE_BUF_SIZE / 4000)
				wait = wait if wait <= 2.0 else 2.0
				time.sleep(wait)

			pbar.close()
			if not ser.telit_rsp('OK', 3, 'ERROR'):
				print('ERROR: File Upload Failed')
				return -1

			if verify and knowhow == '0':
				print("Verifying {} ...".format(filename))
				s = bytearray()
				verified = False
				# clear remaining
				ser.read(4096)
				ser.telit_write('AT#RSCRIPT="{}"'.format(filename))
				timeout = time.time() + filesize / (115200 / 10) + 2.5
				while time.time() < timeout:
					s += ser.read(4096)
					if len(s) == (filesize + 11):
						if (s.startswith(b'\r\n<<<')
							and s.endswith(b'\r\nOK\r\n')
							and s[5:-6] == filedata):
							verified = True
							break
						else:
							break
				if not verified:
					print("ERROR: Verification Failed")
					return -1

		# ser.telit_cmd('AT#CPUMODE=0', 'OK', 0.5)

		if script_mode:
			if scriptext == '.pyo' or scriptext == '.pyc':
				if script_mode == 'enable' or script_mode == 'run':
					if not ser.telit_cmd('AT#ESCRIPT="' + scriptname + '"', 'OK', 0.5):
						return -1
					print("Enabled Script")
				if script_mode == 'run':
					if not ser.telit_cmd('AT#EXECSCR', 'OK', 1):
						return -1
					print("Running Script")
			else:
				print("WARNING: Can't enable or run script, not a compiled script")


		print('SUCCESS')
		return 0

	return -1

def argparse_simple(arg_list):
	""" Returns a tuple of lists: (other, short options, long options) """
	other = []
	opts_short = []
	opts_long = []

	for arg in arg_list:
		if arg[0:2] == '--':
			opts_long.append(arg)
		elif arg[0] == '-':
			opts_short.append(arg)
		else:
			other.append(arg)

	return (other, opts_short, opts_long)

if __name__ == '__main__':
	options = "[--run | --enable] [--verbose] [--com=] [--secure] [--verify]"
	info = "--run or --enable setting is only applied to a script and only to the first supplied"
	usage = "{} <files> {} \n\n{}".format(__file__, options, info)

	if len(sys.argv) == 1:
		print(usage)
		sys.exit(-1)
	else:
		files, na, opts = argparse_simple(sys.argv[1::])

		script_mode = ''
		verbose = False
		com_port = ''
		secure = False
		verify = False
		for opt in opts:
			if '--run' == opt:
				script_mode = "run"
			elif '--enable' == opt:
				if script_mode != "run":
					script_mode = "enable"
			elif '--verbose' == opt:
				verbose = True
			elif '--com=' in opt:
				com_port = opt.split('=')[1]
			elif '--secure' == opt:
				secure = True
			elif '--verify' == opt:
				verify = True
			else:
				print(opt, "Invalid option")
				print(usage)
				sys.exit(-1)

		for f in files:
			if not os.path.isfile(f):
				print(f, 'is not a file, exiting...')
				sys.exit(-1)
			elif len(os.path.basename(f)) > 16:
				print(f, 'filename exceeding 16 characters, exiting...')
				sys.exit(-1)

		status = upload(files, com_port, script_mode, verbose, secure, verify)
		sys.exit(status)
