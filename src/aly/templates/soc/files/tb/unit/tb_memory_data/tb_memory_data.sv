`timescale 1ns/1ps

module tb_memory_data;
    // Data memory load/store semantics test for RV64I widths
    parameter int DMEM_WIDTH = 64;
    parameter int DMEM_DEPTH = 1024;

    logic clk;
    logic rst_n;

    logic [63:0] addr;
    logic [63:0] wdata;
    logic [63:0] rdata;

    // Simple memory model
    logic [63:0] dmem [0:DMEM_DEPTH-1];

    initial begin
        clk = 0;
        rst_n = 0;
        #20 rst_n = 1;

        // Initialize memory
        dmem[0] = 64'hDEADBEEF_DEADBEEF;
        dmem[1] = 64'h00000000_00000000;

        // Perform a load, modify, store, and verify
        addr = 0;
        @(posedge clk);
        rdata = dmem[addr>>3];
        $display("Read rdata=%016h", rdata);

        wdata = rdata + 64'd1;
        dmem[(addr+8)>>3] = wdata; // store to next word
        @(posedge clk);

        if (dmem[(addr+8)>>3] !== wdata) begin
            $display("Data memory verification FAILED: expected %016h got %016h", wdata, dmem[(addr+8)>>3]);
            $stop;
        end else begin
            $display("Data memory verification PASSED");
        end

        $finish;
    end

    always #5 clk = ~clk;
endmodule
