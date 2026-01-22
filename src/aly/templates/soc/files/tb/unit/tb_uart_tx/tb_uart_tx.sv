// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for UART TX Module
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_uart_tx;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    localparam int CLK_FREQ = 100_000_000;
    localparam int BAUD     = 1_000_000;  // Fast baud for simulation
    localparam int CLKS_PER_BIT = CLK_FREQ / BAUD;
    localparam int CLK_PERIOD = 10;  // 100 MHz

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    logic       clk;
    logic       rst_n;
    logic [7:0] data;
    logic       valid;
    logic       ready;
    logic       tx;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    uart_tx #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD(BAUD)
    ) dut (
        .clk_i   (clk),
        .rst_ni  (rst_n),
        .data_i  (data),
        .valid_i (valid),
        .ready_o (ready),
        .tx_o    (tx)
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
    logic [7:0] received_byte;

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
        data  = 0;
        valid = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
    endtask

    // Receive a byte from the TX line
    task automatic receive_byte(output logic [7:0] byte_out);
        // Wait for start bit
        @(negedge tx);
        
        // Sample in middle of bit
        repeat(CLKS_PER_BIT / 2) @(posedge clk);
        
        // Verify start bit
        if (tx != 0) $display("[WARN] Invalid start bit");
        
        // Sample 8 data bits
        for (int i = 0; i < 8; i++) begin
            repeat(CLKS_PER_BIT) @(posedge clk);
            byte_out[i] = tx;
        end
        
        // Sample stop bit
        repeat(CLKS_PER_BIT) @(posedge clk);
        if (tx != 1) $display("[WARN] Invalid stop bit");
    endtask

    // Transmit a byte
    task automatic transmit_byte(input logic [7:0] byte_in);
        wait(ready);
        @(posedge clk);
        data  = byte_in;
        valid = 1;
        @(posedge clk);
        valid = 0;
    endtask

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        $display("============================================");
        $display("ALY UART TX Testbench");
        $display("============================================");
        $display("");

        reset_dut();

        //---------------------------------------------------------------------
        // Test 1: Ready after reset
        //---------------------------------------------------------------------
        check("Ready after reset", ready == 1);
        check("TX idle high", tx == 1);

        //---------------------------------------------------------------------
        // Test 2: Transmit single byte
        //---------------------------------------------------------------------
        $display("[TEST] Transmit 0x55 (alternating bits)");
        fork
            transmit_byte(8'h55);
            receive_byte(received_byte);
        join
        check("Received 0x55 correctly", received_byte == 8'h55);

        //---------------------------------------------------------------------
        // Test 3: Transmit another byte
        //---------------------------------------------------------------------
        $display("[TEST] Transmit 0xAA");
        fork
            transmit_byte(8'hAA);
            receive_byte(received_byte);
        join
        check("Received 0xAA correctly", received_byte == 8'hAA);

        //---------------------------------------------------------------------
        // Test 4: Transmit 0x00
        //---------------------------------------------------------------------
        $display("[TEST] Transmit 0x00");
        fork
            transmit_byte(8'h00);
            receive_byte(received_byte);
        join
        check("Received 0x00 correctly", received_byte == 8'h00);

        //---------------------------------------------------------------------
        // Test 5: Transmit 0xFF
        //---------------------------------------------------------------------
        $display("[TEST] Transmit 0xFF");
        fork
            transmit_byte(8'hFF);
            receive_byte(received_byte);
        join
        check("Received 0xFF correctly", received_byte == 8'hFF);

        //---------------------------------------------------------------------
        // Summary
        //---------------------------------------------------------------------
        #1000;
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
        #10000000;
        $display("[ERROR] Simulation timeout!");
        $display("TEST FAILED");
        $finish;
    end

    //-------------------------------------------------------------------------
    // Waveform Dump
    //-------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_uart_tx.vcd");
        $dumpvars(0, tb_uart_tx);
    end

endmodule : tb_uart_tx
