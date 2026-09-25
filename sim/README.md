# Simulation (cocotb)

Testbench for `rtl/Asynch_FIFO.sv` using cocotb + Icarus Verilog.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Icarus Verilog must also be installed on the system (`apt install iverilog` /
`brew install icarus-verilog`), along with `fst2vcd` from GTKWave
(`apt install gtkwave` / `brew install gtkwave`) for waveform rendering.

## Running

```
make
```

Override DUT parameters or simulator with make variables, e.g.:

```
make DATA_WIDTH=16 DEPTH=32
make SIM=verilator
```

Run a single test with `COCOTB_TESTCASE=<name>`.

## Waveforms

```
make waves
```

runs the full suite with waveform dumping on and renders
`sim_build/Asynch_FIFO.png` from the dump.

```
./generate_waveforms.sh
```

runs `test_back_to_back_streaming`, `test_overlapping_write_and_read`, and
`test_pointer_wraparound` each in isolation and renders one PNG per scenario
into `../docs/waveforms/`, which is what the top-level README embeds.

To render an existing FST dump manually:

```
fst2vcd sim_build/Asynch_FIFO.fst -o sim_build/Asynch_FIFO.vcd
python3 render_waveforms.py sim_build/Asynch_FIFO.vcd out.png "title"
```

## Tests

`test_asynch_fifo.py` holds the cocotb tests.
