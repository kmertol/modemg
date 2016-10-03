Telit Serial-to-GPRS Gateway/Transparent Modem
==============================================

Designed for high reliability, dynamic IP M2M communications.

*Written with Telit Easy Script Python 1.5.2*

## Features

* User defined connection message format which can be used to identify
	devices on the field and give gsm/connection related information
* Extensive and easy configuration through text files over TCP
* Ability to access the AT interface through the current active connection
	(listening with TCPATRUN on a dynamic IP assigned device will not work)
* Watchdog, reset on high downtime, periodic reset to achieve high reliability
* 4K buffer for serial: to hold onto data at downtime

> Lacks SMS configuration (I didn't had time to implement it, and I don't
have a Telit module anymore).

## Portability

I have run it with a GL865, but it will probably work with all the Telit modules that
support *SELINT2* and *Telit Easy Script Python 1.5.2*.

*For Telit Easy Script Python 2.7.2 compatibility:*

* Use the equivalent Python version for the compilation of scripts
* Sleep and timekeeping functions now reside in the `time` module rather than `MOD`
* Remove the `True` and `False` definitions in `helper.py`
* Probably other things that didn't come to my mind

## Setup

* Install Python 1.5.2 for compilation of the Telit modem scripts
* Install Python 3 to use the installation scripts and tools
* Install the required packages for tools using `pip install -r tools/requirements.txt`
* Windows users will need to install *make* and probably have a kind of bash like shell
  environment for some commands to work that are in the *Makefile*

## Makefile configuration

Create a `config.mk` in the base directory. Copy-paste the variables at
the top of the Makefile to *config.mk*, then change them according to your
own system setup to override the ones in the Makefile.

These variables are:

* **python :** path to Python 1.5.2 interpreter
* **dircompile :** path to Dircompile module in the Python 1.5.2 Lib directory
* **AT_PORT :** default serial port to access and send commands to the Telit module
* **TRACE_PORT :** the trace serial port, see [Debugging](#debugging)
* **TCP_PORT :** used for tcp/serial packet testing

## Modem configuration

All of the configurable settings reside in the `default.conf` file; the settings are
explained with the comments in the same file. So before continuing, go have a look
at *default.conf*.

The modem software at boot time loads the *default.conf* file and creates the default settings.
The default value of the settings are not defined inside the scripts, so
you need to have all settings without errors defined in the *default.conf* file.

Now, you probably don't want to mess with the *default.conf* for the time being, and definitely
never on the field. Let's create a `user.conf` file in the same directory: this will be in the
same format as the *default.conf*, but you just need to define the settings you need to override.

If your apn settings are correct, only overriding the `servers` setting will be enough for now.
You also don't need to have section directives in the *.conf* files, I put them just for clarification.

So here is an example *user.conf*, where we define 2 servers; ip:port comma separated. If it fails
connecting to the first it will try connecting to the other servers in sequence and retry all over again.

```ini
servers=133.221.13.98:9800,133.221.13.99:9900
END
```

## Modem Script Installation

*After configuring the Makefile and connecting your Telit module to the serial port:*

Run `make` in the base directory to install or `make debug` to install and listen to the trace port
afterwards.

Default start mode at boot time for the scripts is `AT#STARTMODESCR=1,10`, which runs the script if no
AT command is sent for 10 seconds through the serial port after a reset. You can find and change this
setting inside the `tools/upload.py` script.

If you changed the scripts or the .conf files and you want to reinstall them again: you need
to manually reset the module because the default serial/AT interface is used for the
transparent modem function; therefore it is not possible to send any AT commands for installation
of the scripts. You need to give a reset and try installation before the Telit module starts running
the enabled script.

> The above case may not be entirely true, if your Telit module supports more than one physical AT interface.

## Debugging

### Trace

You can see the output of print statements by listening Telit module's `TRACE_PORT`. To get a more detailed
trace add `verbose_trace=true` in `user.conf`.

> If you want to see the trace but don't have the trace lines connected. You can
set `TRACE_PORT` to the same as `AT_PORT` and set `TRACE_ON_SER = 1` in `boot.py`.
But be aware that this can interfere with the transparent modem function since they
are communicating through the same port.

### Status LED

The Status Led behavior uses Telit's auto mode, adding an extra *Socket Open* case.

* **No Sim/GSM:** Rapid blinking
* **GSM Network Up:** 1 blink in 3 seconds
* **Socket Open:** 1 blink in 1.5 seconds

## AT Bridge

To enter AT bridge mode, through the active TCP connection:

* send `+++`
* wait for reply `OK<CR><LF>`

Now you are in the AT bridge mode; this allows you to access the AT interface directly (AT echo disabled).

To exit AT bridge, use the same sequence you used at entry.

## Configuration in the field (over TCP)

*Maybe some day I will put a script in the tools directory to automate the process. For now, I am giving the
procedure so you can implement it.*

Enter into AT bridge mode, upload the `user.conf` file as you would if you had it connected through the
serial interface and reset the module by sending `AT#ENHRST=1,0` command to have it load the new configuration.

> Updating/Writing `user.conf` is fail safe: an automatic backup is created by the modem software at boot time.

## Magic keywords

I will go over the `connection_message` and `serial_magic` settings, and the magic keywords that you can use which are not completely explained in `default.conf`.

Both of these settings lets you define your own message using a python string, with the magic keywords replaced by their corresponding values.

### connection_message

This string is sent to the server as the first packet when a new connection is established. This way you can use the
Telit modules identification parameters as some kind of a device id, and use it to identify your devices in the field.

* **{imei}, {msisdn}, {imsi}, {iccid}:** these are self-explanatory
* **{csq}:** carrier signal quality (AT+CSQ)
* **{power_uptime}:** uptime in seconds since reboot (more exactly since the first gsm network acquisition)
* **{session_uptime}:** uptime in seconds since activating the gprs pdp context, will reset when gprs is down
* **{gdatavol_total}:** total data usage (AT#GDATAVOL=2), this value is not so reliable since it is not saved into non-volatile
	memory frequently
* **{gdatavol_session}:** session data usage (AT#GDATAVOL=1), unlike total this is more reliable, but will reset if the
	session is down
* **{disconnection}:** total socket/server disconnection count
* **{downtime}:** time in seconds spent not connected to any server the last time
* **{cell}:** gsm cells information parsed nicely (AT#MONI)


*Let's take a look at the default connection message and its output:*

	connection_message='{"imei":"{imei}"}\r\n'

	> {"imei":"357976067027953"}

> I prefer to define the strings to be in a json syntax.

*Now let's define more of the magic keywords:*

	connection_message='{"imei":"{imei}","cell":{cell},"csq":{csq},"power_uptime":{power_uptime},"session_uptime":{session_uptime},"gdatavol_total":{gdatavol_total},"gdatavol_session":{gdatavol_session},"disconnection":{disconnection},"downtime":{downtime}}\r\n'

	> {"imei":"357976067027953","cell":[{"cid":51839,"mcc":286,"mnc":2,"rssi":-100,"lac":54108},{"cid":51984,"mcc":286,"mnc":2,"rssi":-95,"lac":54108},{"cid":52472,"mcc":286,"mnc":2,"rssi":-103,"lac":54108},{"cid":12816,"mcc":286,"mnc":2,"rssi":-103,"lac":54108},{"cid":12815,"mcc":286,"mnc":2,"rssi":-105,"lac":54108},{"cid":52030,"mcc":286,"mnc":2,"rssi":-108,"lac":54108},{"cid":12927,"mcc":286,"mnc":2,"rssi":-108,"lac":54108}],"csq":6,"power_uptime":65154,"session_uptime":40235,"gdatavol_total":[1583085,1206372,376713],"gdatavol_session":[403385,269895,133490],"disconnection":2,"downtime":27}

> You can install my python package [geocell](https://github.com/kmertol/geocell) and use the ***{cell}*** information (if you parse it in python from json it is a list of dictionaries) to get a location estimate without the use of a GPS.

### serial_magic

This string is sent to the serial port on the acquisition of a gsm network.

The magic keywords **{yy}, {MM}, {dd}, {hh}, {mm}, {ss}** correspond to year, month,
day, hour, min, sec respectively. I thought it as a way to automatically synchronize
the clock of the connected device, but you may think it as a kind of template that you
can move inside the code and to signal something to the connected device on some event.
