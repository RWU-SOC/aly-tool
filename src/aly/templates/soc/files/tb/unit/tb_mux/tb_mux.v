// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for MUX Module (Verilog)
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_mux;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    parameter WIDTH = 8;
    parameter N_INPUTS = 4;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    reg  [N_INPUTS*WIDTH-1:0]       data;
    reg  [$clog2(N_INPUTS)-1:0]     sel;
    wire [WIDTH-1:0]                out;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    mux #(
        .WIDTH(WIDTH),
        .N_INPUTS(N_INPUTS)
    ) dut (
        .data_i(data),
        .sel_i (sel),
        .data_o(out)
    );

    //-------------------------------------------------------------------------
    // Test Variables
    //-------------------------------------------------------------------------
    integer test_count;
    integer pass_count;
    integer fail_count;
    integer i;
    reg [WIDTH-1:0] expected;

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

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        test_count = 0;
        pass_count = 0;
        fail_count = 0;
        
        $display("============================================");
        $display("ALY MUX Testbench");
        $display("============================================");
        $display("");

        // Initialize data inputs with distinct values
        data[0*WIDTH +: WIDTH] = 8'hAA;
        data[1*WIDTH +: WIDTH] = 8'hBB;
        data[2*WIDTH +: WIDTH] = 8'hCC;
        data[3*WIDTH +: WIDTH] = 8'hDD;

        // Test each select value
        $display("[TEST] Select operations");
        for (i = 0; i < N_INPUTS; i = i + 1) begin
            sel = i;
            expected = data[i*WIDTH +: WIDTH];
            #10;
            check("MUX select correct", out == expected);
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
    // Waveform Dump
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_mux.vcd");
        $dumpvars(0, tb_mux);
    end

endmodule
