// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for Counter Module
// 
// This is the "Hello World" testbench - if this passes, your ALY setup works!
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_counter;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    localparam int WIDTH = 8;
    localparam int MAX_COUNT = 10;  // Small for quick testing
    localparam int CLK_PERIOD = 10; // 100 MHz

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             en;
    logic             clear;
    logic [WIDTH-1:0] count;
    logic             overflow;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    counter #(
        .WIDTH(WIDTH),
        .MAX_COUNT(MAX_COUNT)
    ) dut (
        .clk_i     (clk),
        .rst_ni    (rst_n),
        .en_i      (en),
        .clear_i   (clear),
        .count_o   (count),
        .overflow_o(overflow)
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
    int test_count = 0;
    int pass_count = 0;
    int fail_count = 0;

    //-------------------------------------------------------------------------
    // Tasks
    //-------------------------------------------------------------------------
    task automatic check(input string name, input logic condition);
        test_count++;
        if (condition) begin
            pass_count++;
            $display("[PASS] %s", name);
        end else begin
            fail_count++;
            $display("[FAIL] %s", name);
        end
    endtask

    task automatic reset_dut();
        rst_n = 0;
        en    = 0;
        clear = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
    endtask

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        $display("============================================");
        $display("ALY Counter Testbench - Hello World Test");
        $display("============================================");
        $display("");

        // Initialize
        reset_dut();

        //---------------------------------------------------------------------
        // Test 1: Counter stays at 0 when disabled
        //---------------------------------------------------------------------
        $display("[TEST] Counter disabled");
        en = 0;
        repeat(10) @(posedge clk);
        check("Counter stays at 0 when disabled", count == 0);

        //---------------------------------------------------------------------
        // Test 2: Counter increments when enabled
        //---------------------------------------------------------------------
        $display("[TEST] Counter enable");
        en = 1;
        repeat(5) @(posedge clk);
        check("Counter increments when enabled", count == 5);

        //---------------------------------------------------------------------
        // Test 3: Counter wraps at MAX_COUNT
        //---------------------------------------------------------------------
        $display("[TEST] Counter overflow");
        // Continue counting until overflow
        repeat(6) @(posedge clk);  // 5 + 6 = 11 > MAX_COUNT
        check("Counter wrapped around", count < 6);
        check("Overflow flag was set", overflow || count == 0);

        //---------------------------------------------------------------------
        // Test 4: Clear works
        //---------------------------------------------------------------------
        $display("[TEST] Clear function");
        clear = 1;
        @(posedge clk);
        clear = 0;
        @(posedge clk);
        check("Clear resets counter", count == 1);  // 1 because en still active

        //---------------------------------------------------------------------
        // Test 5: Reset works
        //---------------------------------------------------------------------
        $display("[TEST] Reset");
        rst_n = 0;
        @(posedge clk);
        check("Reset clears counter", count == 0);

        //---------------------------------------------------------------------
        // Summary
        //---------------------------------------------------------------------
        $display("");
        $display("============================================");
        $display("Test Summary: %0d/%0d passed", pass_count, test_count);
        $display("============================================");

        if (fail_count == 0) begin
            $display("");
            $display("**********************************");
            $display("*        TEST PASSED             *");
            $display("*   ALY simulation is working!   *");
            $display("**********************************");
            $display("");
        end else begin
            $display("");
            $display("**********************************");
            $display("*        TEST FAILED             *");
            $display("**********************************");
            $display("");
        end

        $finish;
    end

    //-------------------------------------------------------------------------
    // Timeout
    //-------------------------------------------------------------------------
    initial begin
        #100000;
        $display("[ERROR] Simulation timeout!");
        $display("TEST FAILED");
        $finish;
    end

    //-------------------------------------------------------------------------
    // Waveform Dump
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_counter.vcd");
        $dumpvars(0, tb_counter);
    end

endmodule : tb_counter
