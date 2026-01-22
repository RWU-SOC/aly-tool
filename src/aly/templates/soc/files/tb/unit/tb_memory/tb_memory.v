// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for Memory Module (Verilog)
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_memory;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    parameter WIDTH = 32;
    parameter DEPTH = 256;
    parameter CLK_PERIOD = 10;
    parameter ADDR_WIDTH = $clog2(DEPTH);

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    reg                    clk;
    reg                    rst_n;
    reg                    a_en;
    reg                    a_we;
    reg  [ADDR_WIDTH-1:0]  a_addr;
    reg  [WIDTH-1:0]       a_wdata;
    reg  [WIDTH/8-1:0]     a_be;
    wire [WIDTH-1:0]       a_rdata;
    reg                    b_en;
    reg  [ADDR_WIDTH-1:0]  b_addr;
    wire [WIDTH-1:0]       b_rdata;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    memory #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .MEM_FILE(""),
        .DUAL_PORT(0)
    ) dut (
        .clk_i    (clk),
        .rst_ni   (rst_n),
        .a_en_i   (a_en),
        .a_we_i   (a_we),
        .a_addr_i (a_addr),
        .a_wdata_i(a_wdata),
        .a_be_i   (a_be),
        .a_rdata_o(a_rdata),
        .b_en_i   (b_en),
        .b_addr_i (b_addr),
        .b_rdata_o(b_rdata)
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
            a_en    = 0;
            a_we    = 0;
            a_addr  = 0;
            a_wdata = 0;
            a_be    = 4'hF;
            b_en    = 0;
            b_addr  = 0;
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
        $display("ALY Memory Testbench");
        $display("============================================");
        $display("");

        reset_dut;

        // Test 1: Write and read back
        $display("[TEST] Write/read operations");
        for (i = 0; i < 16; i = i + 1) begin
            a_en    = 1;
            a_we    = 1;
            a_addr  = i[ADDR_WIDTH-1:0];
            a_wdata = i * 32'h11111111;
            a_be    = 4'hF;
            @(posedge clk);
        end
        a_we = 0;
        
        for (i = 0; i < 16; i = i + 1) begin
            a_addr = i[ADDR_WIDTH-1:0];
            @(posedge clk);
            @(posedge clk);  // Extra cycle for read latency
            check("Read back correct", a_rdata == i * 32'h11111111);
        end

        // Test 2: Byte enable
        $display("[TEST] Byte enable");
        a_we    = 1;
        a_addr  = 0;
        a_wdata = 32'hFFFFFFFF;
        a_be    = 4'h1;  // Only write byte 0
        @(posedge clk);
        a_we = 0;
        @(posedge clk);
        @(posedge clk);
        check("Byte enable works", a_rdata[7:0] == 8'hFF);

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
        $dumpfile("tb_memory.vcd");
        $dumpvars(0, tb_memory);
    end

endmodule
