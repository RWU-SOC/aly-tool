// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for UART TX Module (Verilog)
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_uart_tx;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    parameter CLK_FREQ = 100_000_000;
    parameter BAUD = 115200;
    parameter CLK_PERIOD = 10;  // 100 MHz
    parameter CLKS_PER_BIT = CLK_FREQ / BAUD;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    reg        clk;
    reg        rst_n;
    reg  [7:0] data;
    reg        valid;
    wire       ready;
    wire       tx;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    uart_tx #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD(BAUD)
    ) dut (
        .clk_i  (clk),
        .rst_ni (rst_n),
        .data_i (data),
        .valid_i(valid),
        .ready_o(ready),
        .tx_o   (tx)
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
    reg [7:0] rx_data;
    integer bit_idx;

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
            rst_n = 0;
            data  = 0;
            valid = 0;
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
        $display("ALY UART TX Testbench");
        $display("============================================");
        $display("");

        reset_dut;

        // Test 1: Initial state
        $display("[TEST] Initial state");
        check("TX line idle high", tx == 1);
        check("Ready to transmit", ready == 1);

        // Test 2: Transmit a byte
        $display("[TEST] Transmit byte 0x55");
        data  = 8'h55;
        valid = 1;
        @(posedge clk);
        valid = 0;
        
        // Wait for start bit
        wait(tx == 0);
        check("Start bit detected", tx == 0);
        
        // Sample data bits in the middle of each bit period
        rx_data = 0;
        for (bit_idx = 0; bit_idx < 8; bit_idx = bit_idx + 1) begin
            repeat(CLKS_PER_BIT) @(posedge clk);
            rx_data[bit_idx] = tx;
        end
        
        // Wait for stop bit
        repeat(CLKS_PER_BIT) @(posedge clk);
        check("Stop bit detected", tx == 1);
        check("Data transmitted correctly", rx_data == 8'h55);

        // Wait for ready
        wait(ready == 1);
        check("Ready after transmission", ready == 1);

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
        #50_000_000;  // 50ms timeout for slow baud rate
        $display("[ERROR] Simulation timeout!");
        $finish;
    end

    //-------------------------------------------------------------------------
    // Waveform Dump
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_uart_tx.vcd");
        $dumpvars(0, tb_uart_tx);
    end

endmodule
