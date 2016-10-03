Tools
=====

## upload.py

Uploads scripts/files to the Telit module. It assumes no flow control lines connected; therefore
uses delays as a workaround.

## pactest.py

A test suite that sends/receives data through the serial port and the tcp
socket alternatively.

## compact_conf.py

Just to get rid of the clutter of comment and empty lines in `.conf` files before
uploading. Also to make sure that they end with an `END` line.

## telit_execscr.py

Opens the serial port and sends `AT#EXECSCR` command.

## telit_reset.py

Opens the serial port and sends `AT#ENHRST=1,0` command.
