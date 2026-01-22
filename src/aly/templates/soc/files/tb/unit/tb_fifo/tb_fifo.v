// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for FIFO Module (Verilog)
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_fifo;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    parameter WIDTH = 8;
    parameter DEPTH = 8;
    parameter CLK_PERIOD = 10;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    reg              clk;
    reg              rst_n;
    reg              wr_en;
    reg  [WIDTH-1:0] wr_data;
    wire             full;
    wire             almost_full;
    reg              rd_en;
    wire [WIDTH-1:0] rd_data;
    wire             empty;
    wire             almost_empty;
    wire [$clog2(DEPTH):0] count;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    fifo #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ALMOST_FULL_THRESH(DEPTH-2),
        .ALMOST_EMPTY_THRESH(2)
    ) dut (
        .clk_i         (clk),
        .rst_ni        (rst_n),
        .wr_en_i       (wr_en),
        .wr_data_i     (wr_data),
        .full_o        (full),
        .almost_full_o (almost_full),
        .rd_en_i       (rd_en),
        .rd_data_o     (rd_data),
        .empty_o       (empty),
        .almost_empty_o(almost_empty),
        .count_o       (count)
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
            wr_data = 0;
            rd_en   = 0;
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
        $display("ALY FIFO Testbench");
        $display("============================================");
        $display("");

        reset_dut;

        // Test 1: FIFO starts empty
        $display("[TEST] Initial state");
        check("FIFO starts empty", empty == 1);
        check("FIFO not full", full == 0);

        // Test 2: Write data
        $display("[TEST] Write operations");
        for (i = 0; i < DEPTH; i = i + 1) begin
            wr_en = 1;
            wr_data = i[WIDTH-1:0];
            @(posedge clk);
        end
        wr_en = 0;
        @(posedge clk);
        check("FIFO is full after writes", full == 1);
        check("FIFO not empty", empty == 0);

        // Test 3: Read data
        $display("[TEST] Read operations");
        for (i = 0; i < DEPTH; i = i + 1) begin
            rd_en = 1;
            @(posedge clk);
            check("Read data matches", rd_data == i[WIDTH-1:0]);
        end
        rd_en = 0;
        @(posedge clk);
        check("FIFO is empty after reads", empty == 1);

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
        $dumpfile("tb_fifo.vcd");
        $dumpvars(0, tb_fifo);
    end

endmodule
