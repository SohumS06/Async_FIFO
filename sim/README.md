# Simulation (cocotb)

Testbench for `rtl/Asynch_FIFO.sv` using cocotb + Icarus Verilog.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Icarus Verilog must also be installed on the system (`apt install iverilog` /
`brew install icarus-verilog`).

## Running

```
make
```

Override DUT parameters or simulator with make variables, e.g.:

```
make DATA_WIDTH=16 DEPTH=32
make SIM=verilator
```

A `dump.vcd` is written to `sim_build/` when `WAVES=1` (the default).

## Waveforms

```
make waves
```

runs the test and renders `sim_build/dump.png` from the VCD via
`render_waveforms.py`. To render an existing dump without re-running:

```
python3 render_waveforms.py sim_build/dump.vcd
```

## Tests

`test_asynch_fifo.py` holds the cocotb tests.
