module Asynch_FIFO 

#(
	parameter DATA_WIDTH = 8,
	parameter DEPTH = 16
)
(

	input logic wr_clk, rd_clk,
	input logic wr_reset, rd_reset,
	input logic wr_en, rd_en,
	input logic [DATA_WIDTH-1:0] wr_data,
	
	output logic [DATA_WIDTH-1:0] rd_data,
	output logic full, empty

    );
    
    localparam PTR_WIDTH = $clog2(DEPTH) + 1;
    logic [DATA_WIDTH-1:0] memory[0:DEPTH-1];
    
    logic [PTR_WIDTH-1:0] wr_ptr, rd_ptr;
    logic [PTR_WIDTH-1:0] wr_ptr_gray, rd_ptr_gray;
    logic [PTR_WIDTH-1:0] wr_ptr_gray_1, wr_ptr_gray_sync;
    logic [PTR_WIDTH-1:0] rd_ptr_gray_1, rd_ptr_gray_sync;
    
    logic wr_reset_1, wr_reset_sync, rd_reset_1, rd_reset_sync;
    
    always_ff @(posedge wr_clk or posedge wr_reset) begin
    	if (wr_reset) begin
    		wr_reset_1 <= 1'b1;
    		wr_reset_sync <= 1'b1;
    	end
    	else begin
			wr_reset_1 <= wr_reset;
			wr_reset_sync <= wr_reset_1;
    	end
    end
    
    always_ff @(posedge rd_clk or posedge rd_reset) begin
    	if (rd_reset) begin
    		rd_reset_1 <= 1'b1;
    		rd_reset_sync <= 1'b1;
    	end
    	else begin
			rd_reset_1 <= rd_reset;
			rd_reset_sync <= rd_reset_1;
    	end
    end
    
    always_ff @(posedge wr_clk) begin
		if (wr_reset_sync) wr_ptr <= 0;
    	else if (wr_en) begin
    		memory[wr_ptr[PTR_WIDTH-2:0]] <= wr_data;
    		wr_ptr <= wr_ptr + 1;
		end
	end
	
	always_ff @(posedge rd_clk) begin
		if (rd_reset_sync) rd_ptr <= 0;
    	else if (rd_en) begin
    		rd_ptr <= rd_ptr + 1;
		end
	end

	assign rd_data = memory[rd_ptr[PTR_WIDTH-2:0]];

	assign wr_ptr_gray = wr_ptr ^ (wr_ptr >> 1);
	assign rd_ptr_gray = rd_ptr ^ (rd_ptr >> 1);
	
	always_ff @(posedge rd_clk) begin
		if (rd_reset_sync) begin
			wr_ptr_gray_1 <= 0;
			wr_ptr_gray_sync <= 0;
		end
		else begin
			wr_ptr_gray_1 <= wr_ptr_gray;
			wr_ptr_gray_sync <= wr_ptr_gray_1;
		end
    end
    
    always_ff @(posedge wr_clk) begin
    	if (wr_reset_sync) begin
    		rd_ptr_gray_1 <= 0;
    		rd_ptr_gray_sync <= 0;
    	end
    	else begin
			rd_ptr_gray_1 <= rd_ptr_gray;
			rd_ptr_gray_sync <= rd_ptr_gray_1;
    	end
    end
	
	assign full = (wr_ptr_gray[PTR_WIDTH-1:PTR_WIDTH-2] == ~rd_ptr_gray_sync[PTR_WIDTH-1:PTR_WIDTH-2]) && (wr_ptr_gray[PTR_WIDTH-3:0] == rd_ptr_gray_sync[PTR_WIDTH-3:0]);
	assign empty = (rd_ptr_gray == wr_ptr_gray_sync);
endmodule