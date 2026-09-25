import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly
import random


DEPTH = 16
WR_PERIOD_NS = 10
RD_PERIOD_NS = 7


async def start_clocks(dut):
    cocotb.start_soon(Clock(dut.wr_clk, WR_PERIOD_NS, unit="ns").start())
    cocotb.start_soon(Clock(dut.rd_clk, RD_PERIOD_NS, unit="ns").start())


async def reset_dut(dut):
    dut.wr_reset.value = 1
    dut.rd_reset.value = 1
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0

    for _ in range(4):
        await RisingEdge(dut.wr_clk)
    for _ in range(4):
        await RisingEdge(dut.rd_clk)

    dut.wr_reset.value = 0
    dut.rd_reset.value = 0

    for _ in range(3):
        await RisingEdge(dut.wr_clk)
    for _ in range(3):
        await RisingEdge(dut.rd_clk)


async def settle(dut, cycles=4):
    for _ in range(cycles):
        await RisingEdge(dut.wr_clk)
    for _ in range(cycles):
        await RisingEdge(dut.rd_clk)


async def do_write(dut, data):
    dut.wr_data.value = data
    dut.wr_en.value = 1
    await RisingEdge(dut.wr_clk)
    dut.wr_en.value = 0


async def do_read(dut):
    dut.rd_en.value = 1
    await ReadOnly()
    data = int(dut.rd_data.value)
    await RisingEdge(dut.rd_clk)
    dut.rd_en.value = 0
    return data


@cocotb.test()
async def test_reset_empty(dut):
    await start_clocks(dut)
    await reset_dut(dut)

    assert dut.empty.value == 1
    assert dut.full.value == 0

    await do_write(dut, 0x85)
    await settle(dut)
    assert dut.empty.value == 0

    data = await do_read(dut)
    assert data == 0x85

    await settle(dut)
    assert dut.empty.value == 1

    for i in range(DEPTH):
        await do_write(dut, i)

    await settle(dut)
    assert dut.full.value == 1

    for i in range(DEPTH):
        data = await do_read(dut)
        assert data == i

    await settle(dut)
    assert dut.empty.value == 1


@cocotb.test()
async def test_scoreboard_random(dut):
    await start_clocks(dut)
    await reset_dut(dut)

    expected_queue = []
    total_writes = 200
    writes_done = 0
    reads_done = 0

    async def writer():
        nonlocal writes_done
        while writes_done < total_writes:
            await RisingEdge(dut.wr_clk)
            if dut.full.value == 1 or random.random() < 0.5:
                continue
            data = random.randint(0, 255)
            dut.wr_data.value = data
            dut.wr_en.value = 1
            await RisingEdge(dut.wr_clk)
            dut.wr_en.value = 0
            expected_queue.append(data)
            writes_done += 1

    async def reader():
        nonlocal reads_done
        while reads_done < total_writes:
            await RisingEdge(dut.rd_clk)
            if dut.empty.value == 1 or reads_done >= writes_done or random.random() < 0.5:
                continue
            dut.rd_en.value = 1
            await ReadOnly()
            actual = int(dut.rd_data.value)
            expected = expected_queue[reads_done]
            assert actual == expected, f"read {reads_done}: expected {expected}, got {actual}"
            await RisingEdge(dut.rd_clk)
            dut.rd_en.value = 0
            reads_done += 1

    writer_task = cocotb.start_soon(writer())
    reader_task = cocotb.start_soon(reader())
    await writer_task
    await reader_task


@cocotb.test()
async def test_back_to_back_streaming(dut):
    """Fill the FIFO with gapless writes on wr_clk, then drain it with
    gapless reads on rd_clk."""
    await start_clocks(dut)
    await reset_dut(dut)

    assert dut.empty.value == 1
    assert dut.full.value == 0

    dut.wr_en.value = 1
    for i in range(DEPTH):
        dut.wr_data.value = i
        await RisingEdge(dut.wr_clk)
    dut.wr_en.value = 0

    assert dut.full.value == 1
    assert dut.empty.value == 0

    results = []
    dut.rd_en.value = 1
    for _ in range(DEPTH):
        await ReadOnly()
        results.append(int(dut.rd_data.value))
        await RisingEdge(dut.rd_clk)
    dut.rd_en.value = 0

    assert results == list(range(DEPTH)), f"streamed read mismatch: {results}"
    assert dut.empty.value == 1
    assert dut.full.value == 0


@cocotb.test()
async def test_overlapping_write_and_read(dut):
    """wr_clk and rd_clk are independent, so there is no single shared edge
    to drive both on at once; instead, tightly interleave a write and a
    read so entries are in flight on both clocks at once."""
    await start_clocks(dut)
    await reset_dut(dut)

    expected_queue = []
    for v in (0x11, 0x22):
        await do_write(dut, v)
        expected_queue.append(v)
    await settle(dut)

    for v in (0x33, 0x44, 0x55, 0x66):
        await do_write(dut, v)
        expected_queue.append(v)

        data = await do_read(dut)
        assert data == expected_queue.pop(0)

        assert dut.full.value == 0
        assert dut.empty.value == 0

    while expected_queue:
        data = await do_read(dut)
        assert data == expected_queue.pop(0)

    await settle(dut)
    assert dut.empty.value == 1


@cocotb.test()
async def test_pointer_wraparound(dut):
    """Run several full fill/drain cycles so wr_ptr/rd_ptr wrap past the
    buffer, exercising the gray-code MSB comparison used for full/empty."""
    await start_clocks(dut)
    await reset_dut(dut)

    for rnd in range(3):
        for i in range(DEPTH):
            await do_write(dut, (rnd * DEPTH + i) & 0xFF)
        await settle(dut)
        assert dut.full.value == 1

        for i in range(DEPTH):
            data = await do_read(dut)
            assert data == (rnd * DEPTH + i) & 0xFF
        await settle(dut)
        assert dut.empty.value == 1


@cocotb.test()
async def test_write_when_full_overrun(dut):
    """Document the (unprotected) behavior of asserting wr_en while full.

    This RTL has no guard against writing while full: it silently overwrites
    the oldest, not-yet-read entry and advances wr_ptr anyway, which also
    makes `full` falsely deassert even though data was just lost.
    """
    await start_clocks(dut)
    await reset_dut(dut)

    for i in range(DEPTH):
        await do_write(dut, i)
    assert dut.full.value == 1

    await do_write(dut, 0xAA)
    assert dut.full.value == 0, "overrun write silently clears full instead of being blocked"

    first = await do_read(dut)
    assert first == 0xAA, "overrun write overwrote the oldest unread entry"


@cocotb.test()
async def test_read_when_empty_underrun(dut):
    """Document the (unprotected) behavior of asserting rd_en while empty.

    Nothing blocks rd_en while empty: rd_ptr still advances past wr_ptr,
    which makes `empty` falsely deassert even though no valid data exists.
    """
    await start_clocks(dut)
    await reset_dut(dut)

    assert dut.empty.value == 1

    await do_read(dut)
    assert dut.empty.value == 0, "underrun read desyncs the pointers and clears empty"
