// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for Register File Module (Verilog)
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_regfile;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    parameter WIDTH      = 32;
    parameter DEPTH      = 32;
    parameter READ_PORTS = 2;
    parameter CLK_PERIOD = 10;
    parameter ADDR_WIDTH = $clog2(DEPTH);

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    reg                                      clk;
    reg                                      rst_n;
    reg                                      wr_en;
    reg  [ADDR_WIDTH-1:0]                    wr_addr;
    reg  [WIDTH-1:0]                         wr_data;
    reg  [READ_PORTS*ADDR_WIDTH-1:0]         rd_addr;
    wire [READ_PORTS*WIDTH-1:0]              rd_data;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    regfile #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ZERO_REG(1),
        .READ_PORTS(READ_PORTS)
    ) dut (
        .clk_i    (clk),
        .rst_ni   (rst_n),
        .wr_en_i  (wr_en),
        .wr_addr_i(wr_addr),
        .wr_data_i(wr_data),
        .rd_addr_i(rd_addr),
        .rd_data_o(rd_data)
    );

    //-------------------------------------------------------------------------
    // Clock Generation
    //-------------------------------------------------------------------------
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    //-------------------------------------------------------------------------
    // Test Variables
    //-------------------------------------------------------------------------
    integer test_count;
    integer pass_count;
    integer fail_count;
    integer i;

    //-------------------------------------------------------------------------
    // Tasks
    //-------------------------------------------------------------------------
    task check;
        input [255:0] name;
        input condition;
        begin
            test_count = test_count + 1;
            if (condition) begin
                pass_count = pass_count + 1;
                $display("[PASS] %0s", name);
            end else begin
                fail_count = fail_count + 1;
                $display("[FAIL] %0s", name);
            end
        end
    endtask

    task reset_dut;
        begin
            rst_n   = 0;
            wr_en   = 0;
            wr_addr = 0;
            wr_data = 0;
            rd_addr = 0;
            repeat(5) @(posedge clk);
            rst_n = 1;
            @(posedge clk);
        end
    endtask

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        test_count = 0;
        pass_count = 0;
        fail_count = 0;
        
        $display("============================================");
        $display("ALY Register File Testbench");
        $display("============================================");
        $display("");

        reset_dut;

        // Test 1: Register 0 always reads as 0
        $display("[TEST] Zero register");
        wr_en   = 1;
        wr_addr = 0;
        wr_data = 32'hDEADBEEF;
        @(posedge clk);
        wr_en = 0;
        rd_addr[ADDR_WIDTH-1:0] = 0;
        @(posedge clk);
        check("Register 0 reads as 0", rd_data[WIDTH-1:0] == 0);

        // Test 2: Write and read back
        $display("[TEST] Write/read operations");
        for (i = 1; i < 8; i = i + 1) begin
            wr_en   = 1;
            wr_addr = i[ADDR_WIDTH-1:0];
            wr_data = i * 32'h11111111;
            @(posedge clk);
        end
        wr_en = 0;
        
        for (i = 1; i < 8; i = i + 1) begin
            rd_addr[ADDR_WIDTH-1:0] = i[ADDR_WIDTH-1:0];
            @(posedge clk);
            check("Read back correct", rd_data[WIDTH-1:0] == i * 32'h11111111);
        end

        //---------------------------------------------------------------------
        // Summary
        //---------------------------------------------------------------------
        $display("");
        $display("============================================");
        $display("Test Summary: %0d/%0d passed", pass_count, test_count);
        $display("============================================");

        if (fail_count == 0) begin
            $display("TEST PASSED");
        end else begin
            $display("TEST FAILED");
        end

        $finish;
    end

    //-------------------------------------------------------------------------
    // Timeout
    //-------------------------------------------------------------------------
    initial begin
        #1000000;
        $display("[ERROR] Simulation timeout!");
        $finish;
    end

    //-------------------------------------------------------------------------
    // Waveform Dump
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_regfile.vcd");
        $dumpvars(0, tb_regfile);
    end

endmodule
