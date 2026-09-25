import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def start_clocks(dut, wr_period_ns=10, rd_period_ns=7):
    cocotb.start_soon(Clock(dut.wr_clk, wr_period_ns, units="ns").start())
    cocotb.start_soon(Clock(dut.rd_clk, rd_period_ns, units="ns").start())


async def reset_dut(dut):
    dut.wr_reset.value = 1
    dut.rd_reset.value = 1
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    await Timer(50, units="ns")
    dut.wr_reset.value = 0
    dut.rd_reset.value = 0
    await RisingEdge(dut.wr_clk)
    await RisingEdge(dut.rd_clk)


@cocotb.test()
async def test_placeholder(dut):
    await start_clocks(dut)
    await reset_dut(dut)
    await Timer(100, units="ns")
