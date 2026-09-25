`timescale 1ns / 1ps

module asynch_FIFO_axi_stream

#(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 16
)
(
    input  logic s_axis_aclk,
    input  logic s_axis_aresetn,
    input  logic m_axis_aclk,
    input  logic m_axis_aresetn,

    input  logic [DATA_WIDTH-1:0] s_axis_tdata,
    input  logic                  s_axis_tvalid,
    output logic                  s_axis_tready,

    output logic [DATA_WIDTH-1:0] m_axis_tdata,
    output logic                  m_axis_tvalid,
    input  logic                  m_axis_tready
    );

    logic full_i;
    logic empty_i;

    Asynch_FIFO #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH)
    ) inst (
        .wr_clk(s_axis_aclk),
        .rd_clk(m_axis_aclk),
        .wr_reset(~s_axis_aresetn),
        .rd_reset(~m_axis_aresetn),
        .wr_en(s_axis_tvalid & s_axis_tready),
        .wr_data(s_axis_tdata),
        .rd_en(m_axis_tready & m_axis_tvalid),
        .rd_data(m_axis_tdata),
        .full(full_i),
        .empty(empty_i)
    );

    assign s_axis_tready = ~full_i;
    assign m_axis_tvalid = ~empty_i;
endmodule
