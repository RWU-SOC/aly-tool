// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for GPIO Module
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_gpio;

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
    logic [31:0]      addr;
    logic [31:0]      wdata;
    logic             we;
    logic             re;
    logic [31:0]      rdata;
    logic [WIDTH-1:0] gpio_in;
    logic [WIDTH-1:0] gpio_out;
    logic [WIDTH-1:0] gpio_oe;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    gpio #(
        .WIDTH(WIDTH)
    ) dut (
        .clk_i    (clk),
        .rst_ni   (rst_n),
        .addr_i   (addr),
        .wdata_i  (wdata),
        .we_i     (we),
        .re_i     (re),
        .rdata_o  (rdata),
        .gpio_i   (gpio_in),
        .gpio_o   (gpio_out),
        .gpio_oe_o(gpio_oe)
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
        rst_n   = 0;
        addr    = 0;
        wdata   = 0;
        we      = 0;
        re      = 0;
        gpio_in = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
    endtask

    task automatic write_reg(input logic [31:0] address, input logic [31:0] data);
        @(posedge clk);
        addr  = address;
        wdata = data;
        we    = 1;
        @(posedge clk);
        we    = 0;
    endtask

    task automatic read_reg(input logic [31:0] address, output logic [31:0] data);
        @(posedge clk);
        addr = address;
        re   = 1;
        @(posedge clk);
        data = rdata;
        re   = 0;
    endtask

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    logic [31:0] read_data;

    initial begin
        $display("============================================");
        $display("ALY GPIO Testbench");
        $display("============================================");
        $display("");

        reset_dut();

        //---------------------------------------------------------------------
        // Test 1: Reset state
        //---------------------------------------------------------------------
        $display("[TEST] Reset state");
        check("Output is 0 after reset", gpio_out == 0);
        check("Output enable is 0 after reset", gpio_oe == 0);

        //---------------------------------------------------------------------
        // Test 2: Write data register
        //---------------------------------------------------------------------
        $display("[TEST] Write data register");
        write_reg(32'h0, 32'hA5);
        @(posedge clk);
        check("Data written to output", gpio_out == 8'hA5);

        //---------------------------------------------------------------------
        // Test 3: Write direction register
        //---------------------------------------------------------------------
        $display("[TEST] Write direction register");
        write_reg(32'h4, 32'hF0);
        @(posedge clk);
        check("Direction set correctly", gpio_oe == 8'hF0);

        //---------------------------------------------------------------------
        // Test 4: Read data register
        //---------------------------------------------------------------------
        $display("[TEST] Read data register");
        read_reg(32'h0, read_data);
        check("Read data matches written", read_data[7:0] == 8'hA5);

        //---------------------------------------------------------------------
        // Test 5: Read input register
        //---------------------------------------------------------------------
        $display("[TEST] Read input register");
        gpio_in = 8'h3C;
        repeat(3) @(posedge clk);  // Allow synchronization
        read_reg(32'h8, read_data);
        check("Input read correctly", read_data[7:0] == 8'h3C);

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
        $display("TEST FAILED");
        $finish;
    end

    //-------------------------------------------------------------------------
    // Waveform Dump
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_gpio.vcd");
        $dumpvars(0, tb_gpio);
    end

endmodule : tb_gpio
