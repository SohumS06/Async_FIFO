# Asynchronous FIFO with AXI4-Stream

The RTL and its logic here are hand-written by me. I also wrote some of the cocotb testbenches myself; AI assistance filled in the rest of the test coverage, fixed a testbench read-timing bug that was giving false failures, and wrote the waveform-rendering script, but the FIFO and the AXI4-Stream wrapper are untouched by it.

This is a dual-clock (asynchronous) FIFO with an AXI4-Stream wrapper on top of it, so it can drop into anything expecting a standard AXIS handshake instead of raw read/write enables, while the write and read sides run on independent clocks.

## What's in here

`rtl/Asynch_FIFO.sv` is the actual FIFO: a circular buffer with separate write and read pointers, one bit wider than needed to address the memory so wrapping the pointer around lets `full` and `empty` be told apart with simple pointer comparisons instead of a separate counter. `wr_ptr`/`rd_ptr` are Gray-coded and passed through 2-flop synchronizers into the opposite clock domain before being compared, which is what makes crossing between `wr_clk` and `rd_clk` safe. Each domain resets independently (`wr_reset`/`rd_reset`), each through its own 2-flop async-assert/sync-deassert reset synchronizer. The read data path is combinational (first-word-fall-through), so `rd_data` reflects the head of the queue as soon as it's there, not one cycle after `rd_en`. `DATA_WIDTH` and `DEPTH` are both parameters (`DEPTH` must be a power of 2 for the pointer-wrap comparison to work).

`rtl/asynch_FIFO_axi_stream.sv` wraps the FIFO in an AXI4-Stream slave/master interface — `s_axis_tdata`/`s_axis_tvalid`/`s_axis_tready` on the write side (`s_axis_aclk`/`s_axis_aresetn`), `m_axis_tdata`/`m_axis_tvalid`/`m_axis_tready` on the read side (`m_axis_aclk`/`m_axis_aresetn`) — so `wr_en`/`rd_en` just become the AND of valid and ready on each side.

`sim/test_asynch_fifo.py` is the cocotb testbench. It covers reset behavior, basic write/read, filling and draining, gapless back-to-back writes and reads, overlapping writes and reads running on their own independent clocks, pointer wraparound, and what happens if you assert `wr_en` while full or `rd_en` while empty (spoiler: nothing stops you, and it'll quietly corrupt data — there's no overflow/underflow protection in this design, so that's on whatever's driving it).

`sim/render_waveforms.py` renders a cocotb waveform dump to a PNG. `sim/generate_waveforms.sh` runs three of the tests in isolation with waveform dumping on and renders each to `docs/waveforms/`.

## Simulation

I'm using cocotb with Icarus Verilog for simulation. `cd sim && make` runs the full test suite.

```
cd sim
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make
```

## Waveforms

**Fill then drain** — gapless writes until full, then gapless reads until empty, each on its own clock. `full` and `empty` each pulse for exactly one cycle at the transition points, and the write/read pointers count straight up without resetting.

![Fill then drain](docs/waveforms/fill_then_drain.png)

**Overlapping write + read** — once the FIFO has a couple of entries in it, writes on `wr_clk` and reads on `rd_clk` happen concurrently instead of in lockstep, and the data still comes out in the order it went in.

![Overlapping write and read](docs/waveforms/overlapping_write_and_read.png)

**Pointer wraparound** — three full fill/drain rounds back to back, enough for both pointers to wrap past the top of the buffer twice. Data stays consistent across the wrap, which is the whole point of using a pointer MSB instead of a separate counter for the full/empty logic.

![Pointer wraparound](docs/waveforms/pointer_wraparound.png)
