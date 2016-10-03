#!/usr/bin/env python
# Copyright (c) 2016 Kaan Mertol
# Licensed under the GNU GPLv3. See the accompanying LICENSE file
import sys

def compact(s):
	add_end = False

	s = s.strip()
	if not s.endswith("END"):
		add_end = True

	lines = s.splitlines()
	new = []
	for line in lines:
		line = line.strip()
		if len(line) <= 2 or line[0] == '[' or line[0] == '#':
			continue
		new.append(line)

	if add_end:
		new.append("END")

	return '\n'.join(new)

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print(sys.argv[0], "input_file", "output_file")
		sys.exit(-1)

	with open(sys.argv[1]) as f:
		s = f.read()

	s = compact(s)

	with open(sys.argv[2], 'w') as f:
		f.write(s)

	sys.exit(0)

