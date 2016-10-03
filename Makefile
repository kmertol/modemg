########################   To config.mk  #####################################
python = "/c/Program Files (x86)/Telit_Python_152/python.exe"
dircompile = "/c/Program Files (x86)/Telit_Python_152/Lib/Dircompile.py"
AT_PORT = COM9
TRACE_PORT = COM9
TCP_PORT = 40960
##############################################################################

# Override the above variables in the included file, so that you can change
# them easily without committing them to revision control
-include config.mk

# To be able to work without user.conf if not supplied
OUT := out/boot.pyo out/modemg.pyo out/helper.pyo out/default.conf
ifneq (,$(wildcard user.conf))
	OUT := $(OUT) out/user.conf
	compact_user_conf = python tools/compact_conf.py user.conf out/user.conf
else
	compact_user_conf =
endif

all: install

help:
	@echo "debug                - upload, run, trace"
	@echo "reset_debug          - reset, upload, run, trace"
	@echo "install              - upload, run"
	@echo "install_and_test:    - upload, run, pactest"
	@echo "change_conf          - reupload user.conf and run"
	@echo "test                 - pactest"
	@echo reset
	@echo clean

modemg: modemg.py helper.py boot.py
	mkdir -p out
	${python} -S -OO ${dircompile} modemg.py
	${python} -S -OO ${dircompile} helper.py
	${python} -S -OO ${dircompile} boot.py
	mv *.pyo out
	python tools/compact_conf.py default.conf out/default.conf
	$(compact_user_conf)

debug: modemg
	python tools/upload.py ${OUT} --com=${AT_PORT} --verbose --run
	python -m serial.tools.miniterm ${TRACE_PORT} 115200

reset_debug: modemg
	python tools/telit_reset.py ${AT_PORT}
	python tools/upload.py ${OUT} --com=${AT_PORT} --verbose --run
	python -m serial.tools.miniterm ${TRACE_PORT} 115200

install: modemg
	python tools/upload.py ${OUT} --com=${AT_PORT} --verbose --run --verify

install_and_test: modemg
	python tools/upload.py ${OUT} --com=${AT_PORT} --verbose --run --verify
	python tools/pactest.py ${AT_PORT} ${TCP_PORT} 4000 1

change_conf:
	$(compact_user_conf)
	python tools/upload.py out/user.conf --com=${AT_PORT} --verbose
	python tools/telit_execscr.py ${AT_PORT}

test:
	python tools/pactest.py ${AT_PORT} ${TCP_PORT} 4000 1

reset:
	python tools/telit_reset.py ${AT_PORT}

clean:
	rm -f *.pyo out/*
