// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for Multiplexer Module
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_mux;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    localparam int WIDTH = 8;
    localparam int N_INPUTS = 4;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    logic [N_INPUTS-1:0][WIDTH-1:0] data_in;
    logic [$clog2(N_INPUTS)-1:0]    sel;
    logic [N_INPUTS-1:0]            sel_oh;
    logic [WIDTH-1:0]               data_out_bin;
    logic [WIDTH-1:0]               data_out_oh;

    //-------------------------------------------------------------------------
    // DUT - Binary select mux
    //-------------------------------------------------------------------------
    mux #(
        .WIDTH(WIDTH),
        .N_INPUTS(N_INPUTS),
        .ONE_HOT(0)
    ) dut_binary (
        .data_i   (data_in),
        .sel_i    (sel),
        .sel_oh_i (sel_oh),
        .data_o   (data_out_bin)
    );

    //-------------------------------------------------------------------------
    // DUT - One-hot select mux
    //-------------------------------------------------------------------------
    mux #(
        .WIDTH(WIDTH),
        .N_INPUTS(N_INPUTS),
        .ONE_HOT(1)
    ) dut_onehot (
        .data_i   (data_in),
        .sel_i    (sel),
        .sel_oh_i (sel_oh),
        .data_o   (data_out_oh)
    );

    //-------------------------------------------------------------------------
    // Test Variables
    //-------------------------------------------------------------------------
    int test_count = 0;
    int pass_count = 0;
    int fail_count = 0;

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

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        $display("============================================");
        $display("ALY Multiplexer Testbench");
        $display("============================================");
        $display("");

        // Initialize inputs with distinct values
        for (int i = 0; i < N_INPUTS; i++) begin
            data_in[i] = (i + 1) * 10;  // 10, 20, 30, 40
        end

        //---------------------------------------------------------------------
        // Test 1: Binary select mux
        //---------------------------------------------------------------------
        $display("[TEST] Binary select mux");
        for (int i = 0; i < N_INPUTS; i++) begin
            sel = i[$clog2(N_INPUTS)-1:0];
            #1;
            check($sformatf("Binary sel=%0d -> data=%0d", i, (i+1)*10), 
                  data_out_bin == (i + 1) * 10);
        end

        //---------------------------------------------------------------------
        // Test 2: One-hot select mux
        //---------------------------------------------------------------------
        $display("[TEST] One-hot select mux");
        for (int i = 0; i < N_INPUTS; i++) begin
            sel_oh = (1 << i);
            #1;
            check($sformatf("One-hot sel=%b -> data=%0d", sel_oh, (i+1)*10), 
                  data_out_oh == (i + 1) * 10);
        end

        //---------------------------------------------------------------------
        // Test 3: Change input values
        //---------------------------------------------------------------------
        $display("[TEST] Dynamic input changes");
        data_in[0] = 8'hAA;
        data_in[1] = 8'hBB;
        data_in[2] = 8'hCC;
        data_in[3] = 8'hDD;
        
        sel = 2;
        #1;
        check("Select input 2 (0xCC)", data_out_bin == 8'hCC);
        
        sel_oh = 4'b1000;
        #1;
        check("One-hot select input 3 (0xDD)", data_out_oh == 8'hDD);

        //---------------------------------------------------------------------
        // Summary
        //---------------------------------------------------------------------
        $display("");
        $display("============================================");
        $display("Test Summary: %0d/%0d passed", pass_count, test_count);
        $display("============================================");

        if (fail_count == 0) begin
            $display("ALL TESTS PASSED!");
        end else begin
            $display("SOME TESTS FAILED!");
        end

        $finish;
    end

endmodule
