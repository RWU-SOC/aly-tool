// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for Shift Register Module
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_shift_reg;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    localparam int WIDTH = 8;
    localparam int CLK_PERIOD = 10;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             en;
    logic             dir;
    logic             load;
    logic             serial_in;
    logic [WIDTH-1:0] parallel_in;
    logic [WIDTH-1:0] data_out;
    logic             serial_out;

    //-------------------------------------------------------------------------
    // DUT - Linear shift register
    //-------------------------------------------------------------------------
    shift_reg #(
        .WIDTH(WIDTH),
        .CIRCULAR(0)
    ) dut_linear (
        .clk_i     (clk),
        .rst_ni    (rst_n),
        .en_i      (en),
        .dir_i     (dir),
        .load_i    (load),
        .serial_i  (serial_in),
        .parallel_i(parallel_in),
        .data_o    (data_out),
        .serial_o  (serial_out)
    );

    // Circular shift register
    logic [WIDTH-1:0] circ_data_out;
    logic             circ_serial_out;

    shift_reg #(
        .WIDTH(WIDTH),
        .CIRCULAR(1)
    ) dut_circular (
        .clk_i     (clk),
        .rst_ni    (rst_n),
        .en_i      (en),
        .dir_i     (dir),
        .load_i    (load),
        .serial_i  (serial_in),
        .parallel_i(parallel_in),
        .data_o    (circ_data_out),
        .serial_o  (circ_serial_out)
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
        rst_n       = 0;
        en          = 0;
        dir         = 0;
        load        = 0;
        serial_in   = 0;
        parallel_in = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
    endtask

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        $display("============================================");
        $display("ALY Shift Register Testbench");
        $display("============================================");
        $display("");

        reset_dut();

        //---------------------------------------------------------------------
        // Test 1: Parallel load
        //---------------------------------------------------------------------
        $display("[TEST] Parallel load");
        
        parallel_in = 8'hA5;
        load = 1;
        @(posedge clk);
        load = 0;
        @(posedge clk);
        
        check("Parallel load value", data_out == 8'hA5);

        //---------------------------------------------------------------------
        // Test 2: Left shift
        //---------------------------------------------------------------------
        $display("[TEST] Left shift");
        
        parallel_in = 8'h01;
        load = 1;
        @(posedge clk);
        load = 0;
        
        dir = 0;  // Left shift
        en  = 1;
        serial_in = 0;
        
        @(posedge clk);  // 0x01 -> 0x02
        check("Left shift 1", data_out == 8'h02);
        
        @(posedge clk);  // 0x02 -> 0x04
        check("Left shift 2", data_out == 8'h04);
        
        @(posedge clk);  // 0x04 -> 0x08
        check("Left shift 3", data_out == 8'h08);
        
        en = 0;
        @(posedge clk);

        //---------------------------------------------------------------------
        // Test 3: Right shift
        //---------------------------------------------------------------------
        $display("[TEST] Right shift");
        
        parallel_in = 8'h80;
        load = 1;
        @(posedge clk);
        load = 0;
        
        dir = 1;  // Right shift
        en  = 1;
        serial_in = 0;
        
        @(posedge clk);  // 0x80 -> 0x40
        check("Right shift 1", data_out == 8'h40);
        
        @(posedge clk);  // 0x40 -> 0x20
        check("Right shift 2", data_out == 8'h20);
        
        en = 0;
        @(posedge clk);

        //---------------------------------------------------------------------
        // Test 4: Circular shift
        //---------------------------------------------------------------------
        $display("[TEST] Circular shift");
        
        parallel_in = 8'h81;  // 10000001
        load = 1;
        @(posedge clk);
        load = 0;
        
        dir = 0;  // Left shift
        en  = 1;
        
        @(posedge clk);  // 10000001 -> 00000011 (circular left)
        check("Circular left shift", circ_data_out == 8'h03);
        
        en = 0;
        @(posedge clk);

        //---------------------------------------------------------------------
        // Test 5: Serial output
        //---------------------------------------------------------------------
        $display("[TEST] Serial output");
        
        parallel_in = 8'hF0;
        load = 1;
        @(posedge clk);
        load = 0;
        
        dir = 0;  // Left shift - MSB comes out
        en  = 1;
        
        check("Serial out is MSB (1)", serial_out == 1);
        
        @(posedge clk);
        check("Serial out after shift (1)", serial_out == 1);
        
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);
        check("Serial out after 4 shifts (0)", serial_out == 0);
        
        en = 0;

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

    // Timeout
    initial begin
        #100000;
        $display("[ERROR] Simulation timeout!");
        $finish;
    end

endmodule
