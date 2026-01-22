// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for FIFO Module
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_fifo;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    localparam int WIDTH = 8;
    localparam int DEPTH = 8;
    localparam int CLK_PERIOD = 10;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             wr_en;
    logic [WIDTH-1:0] wr_data;
    logic             full;
    logic             almost_full;
    logic             rd_en;
    logic [WIDTH-1:0] rd_data;
    logic             empty;
    logic             almost_empty;
    logic [$clog2(DEPTH):0] count;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    fifo #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ALMOST_FULL_THRESH(DEPTH - 2),
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
        rst_n   = 0;
        wr_en   = 0;
        rd_en   = 0;
        wr_data = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
    endtask

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        $display("============================================");
        $display("ALY FIFO Testbench");
        $display("============================================");
        $display("");

        reset_dut();

        //---------------------------------------------------------------------
        // Test 1: Empty after reset
        //---------------------------------------------------------------------
        $display("[TEST] Empty after reset");
        check("FIFO is empty", empty == 1);
        check("FIFO not full", full == 0);
        check("Count is 0", count == 0);

        //---------------------------------------------------------------------
        // Test 2: Write to FIFO
        //---------------------------------------------------------------------
        $display("[TEST] Write operations");
        for (int i = 0; i < DEPTH; i++) begin
            wr_en   = 1;
            wr_data = i[WIDTH-1:0];
            @(posedge clk);
        end
        wr_en = 0;
        @(posedge clk);
        
        check("FIFO is full", full == 1);
        check("FIFO not empty", empty == 0);
        check("Count is DEPTH", count == DEPTH);

        //---------------------------------------------------------------------
        // Test 3: Read from FIFO
        //---------------------------------------------------------------------
        $display("[TEST] Read operations");
        for (int i = 0; i < DEPTH; i++) begin
            check($sformatf("Read data[%0d] = %0d", i, i), rd_data == i[WIDTH-1:0]);
            rd_en = 1;
            @(posedge clk);
        end
        rd_en = 0;
        @(posedge clk);
        
        check("FIFO is empty after reads", empty == 1);
        check("Count is 0 after reads", count == 0);

        //---------------------------------------------------------------------
        // Test 4: Simultaneous read/write
        //---------------------------------------------------------------------
        $display("[TEST] Simultaneous read/write");
        // First fill half
        for (int i = 0; i < DEPTH/2; i++) begin
            wr_en   = 1;
            wr_data = i[WIDTH-1:0];
            @(posedge clk);
        end
        wr_en = 0;
        @(posedge clk);
        
        // Simultaneous read/write
        wr_en   = 1;
        rd_en   = 1;
        wr_data = 8'hAA;
        @(posedge clk);
        wr_en = 0;
        rd_en = 0;
        @(posedge clk);
        
        check("Count unchanged after simul R/W", count == DEPTH/2);

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
