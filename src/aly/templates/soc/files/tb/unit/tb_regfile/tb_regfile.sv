// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Testbench for Register File Module
//-----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_regfile;

    //-------------------------------------------------------------------------
    // Parameters
    //-------------------------------------------------------------------------
    localparam int WIDTH = 32;
    localparam int DEPTH = 8;
    localparam int READ_PORTS = 2;
    localparam int CLK_PERIOD = 10;

    //-------------------------------------------------------------------------
    // Signals
    //-------------------------------------------------------------------------
    logic                          clk;
    logic                          rst_n;
    logic                          wr_en;
    logic [$clog2(DEPTH)-1:0]      wr_addr;
    logic [WIDTH-1:0]              wr_data;
    logic [READ_PORTS-1:0][$clog2(DEPTH)-1:0] rd_addr;
    logic [READ_PORTS-1:0][WIDTH-1:0]         rd_data;

    //-------------------------------------------------------------------------
    // DUT
    //-------------------------------------------------------------------------
    regfile #(
        .WIDTH(WIDTH),
        .DEPTH(DEPTH),
        .ZERO_REG(1),
        .READ_PORTS(READ_PORTS)
    ) dut (
        .clk_i    (clk),
        .rst_ni   (rst_n),
        .wr_en_i  (wr_en),
        .wr_addr_i(wr_addr),
        .wr_data_i(wr_data),
        .rd_addr_i(rd_addr),
        .rd_data_o(rd_data)
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
        wr_addr = 0;
        wr_data = 0;
        rd_addr = '{default: 0};
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
    endtask

    //-------------------------------------------------------------------------
    // Test Sequence
    //-------------------------------------------------------------------------
    initial begin
        $display("============================================");
        $display("ALY Register File Testbench");
        $display("============================================");
        $display("");

        reset_dut();

        //---------------------------------------------------------------------
        // Test 1: Register 0 always zero
        //---------------------------------------------------------------------
        $display("[TEST] Register 0 hardwired to zero");
        
        // Try to write to register 0
        wr_en   = 1;
        wr_addr = 0;
        wr_data = 32'hDEADBEEF;
        @(posedge clk);
        wr_en = 0;
        @(posedge clk);
        
        rd_addr[0] = 0;
        #1;
        check("Reg 0 reads as zero after write attempt", rd_data[0] == 0);

        //---------------------------------------------------------------------
        // Test 2: Write and read back
        //---------------------------------------------------------------------
        $display("[TEST] Write and read back");
        
        for (int i = 1; i < DEPTH; i++) begin
            wr_en   = 1;
            wr_addr = i[$clog2(DEPTH)-1:0];
            wr_data = i * 100;
            @(posedge clk);
        end
        wr_en = 0;
        @(posedge clk);
        
        for (int i = 1; i < DEPTH; i++) begin
            rd_addr[0] = i[$clog2(DEPTH)-1:0];
            #1;
            check($sformatf("Reg[%0d] = %0d", i, i*100), rd_data[0] == i * 100);
        end

        //---------------------------------------------------------------------
        // Test 3: Dual read ports
        //---------------------------------------------------------------------
        $display("[TEST] Dual read ports");
        
        rd_addr[0] = 1;
        rd_addr[1] = 2;
        #1;
        check("Port 0 reads Reg[1]", rd_data[0] == 100);
        check("Port 1 reads Reg[2]", rd_data[1] == 200);

        //---------------------------------------------------------------------
        // Test 4: Write-through (read during write)
        //---------------------------------------------------------------------
        $display("[TEST] Write-through");
        
        rd_addr[0] = 3;  // About to be written
        wr_en   = 1;
        wr_addr = 3;
        wr_data = 32'h12345678;
        #1;
        check("Write-through: new value visible immediately", 
              rd_data[0] == 32'h12345678);
        @(posedge clk);
        wr_en = 0;

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
