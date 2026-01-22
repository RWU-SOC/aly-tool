// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for GPIO Module (Verilog)
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_gpio;

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
    reg  [31:0]      addr;
    reg  [31:0]      wdata;
    reg              we;
    reg              re;
    wire [31:0]      rdata;
    reg  [WIDTH-1:0] gpio_in;
    wire [WIDTH-1:0] gpio_out;
    wire [WIDTH-1:0] gpio_oe;

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
            rst_n   = 0;
            addr    = 0;
            wdata   = 0;
            we      = 0;
            re      = 0;
            gpio_in = 0;
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
        $display("ALY GPIO Testbench");
        $display("============================================");
        $display("");

        reset_dut;

        // Test 1: Write to data register
        $display("[TEST] Data register write");
        addr  = 32'h0;  // REG_DATA
        wdata = 32'hA5;
        we    = 1;
        @(posedge clk);
        we = 0;
        @(posedge clk);
        check("Data output correct", gpio_out == 8'hA5);

        // Test 2: Write to direction register
        $display("[TEST] Direction register write");
        addr  = 32'h4;  // REG_DIR
        wdata = 32'hFF;
        we    = 1;
        @(posedge clk);
        we = 0;
        @(posedge clk);
        check("Direction output correct", gpio_oe == 8'hFF);

        // Test 3: Read input register
        $display("[TEST] Input register read");
        gpio_in = 8'h5A;
        @(posedge clk);
        @(posedge clk);  // Sync cycle
        addr = 32'h8;  // REG_INPUT
        re   = 1;
        @(posedge clk);
        check("Input read correct", rdata[7:0] == 8'h5A);
        re = 0;

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
        $dumpfile("tb_gpio.vcd");
        $dumpvars(0, tb_gpio);
    end

endmodule
