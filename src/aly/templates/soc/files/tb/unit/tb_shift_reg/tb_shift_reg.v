// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for Shift Register Module (Verilog)
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_shift_reg;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    parameter WIDTH = 8;
    parameter CLK_PERIOD = 10;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    reg              clk;
    reg              rst_n;
    reg              en;
    reg              dir;
    reg              load;
    reg              serial_in;
    reg  [WIDTH-1:0] parallel_in;
    wire [WIDTH-1:0] data;
    wire             serial_out;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    shift_reg #(
        .WIDTH(WIDTH),
        .DEPTH(1),
        .CIRCULAR(0)
    ) dut (
        .clk_i     (clk),
        .rst_ni    (rst_n),
        .en_i      (en),
        .dir_i     (dir),
        .load_i    (load),
        .serial_i  (serial_in),
        .parallel_i(parallel_in),
        .data_o    (data),
        .serial_o  (serial_out)
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
            rst_n       = 0;
            en          = 0;
            dir         = 0;
            load        = 0;
            serial_in   = 0;
            parallel_in = 0;
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
        $display("ALY Shift Register Testbench");
        $display("============================================");
        $display("");

        reset_dut;

        // Test 1: Parallel load
        $display("[TEST] Parallel load");
        parallel_in = 8'hA5;
        load = 1;
        @(posedge clk);
        load = 0;
        @(posedge clk);
        check("Parallel load works", data == 8'hA5);

        // Test 2: Left shift
        $display("[TEST] Left shift");
        en = 1;
        dir = 0;  // Left
        serial_in = 1;
        @(posedge clk);
        check("Left shift works", data == 8'h4B);  // A5 << 1 | 1 = 4B

        // Test 3: Right shift
        $display("[TEST] Right shift");
        dir = 1;  // Right
        serial_in = 0;
        @(posedge clk);
        check("Right shift works", data == 8'h25);  // 4B >> 1 = 25

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
        #100000;
        $display("[ERROR] Simulation timeout!");
        $finish;
    end

    //-------------------------------------------------------------------------
    // Waveform Dump
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_shift_reg.vcd");
        $dumpvars(0, tb_shift_reg);
    end

endmodule
