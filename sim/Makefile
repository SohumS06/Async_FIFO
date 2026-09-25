SIM ?= icarus
TOPLEVEL_LANG ?= verilog

PWD := $(shell pwd)

DATA_WIDTH ?= 8
DEPTH ?= 16

VERILOG_SOURCES = $(PWD)/../rtl/Asynch_FIFO.sv

TOPLEVEL = Asynch_FIFO
MODULE = test_asynch_fifo

COMPILE_ARGS += -P $(TOPLEVEL).DATA_WIDTH=$(DATA_WIDTH)
COMPILE_ARGS += -P $(TOPLEVEL).DEPTH=$(DEPTH)

WAVES ?= 1

include $(shell cocotb-config --makefiles)/Makefile.sim

waves: sim
	fst2vcd sim_build/Asynch_FIFO.fst -o sim_build/Asynch_FIFO.vcd
	python3 render_waveforms.py sim_build/Asynch_FIFO.vcd

docs-waveforms:
	./generate_waveforms.sh

.PHONY: waves docs-waveforms
