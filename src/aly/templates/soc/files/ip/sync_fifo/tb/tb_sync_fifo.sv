// Testbench for Synchronous FIFO - SystemVerilog
// =============================================================================

`timescale 1ns/1ps

module tb_sync_fifo;

    // ==========================================================================
    // Parameters
    // ==========================================================================
    parameter DATA_WIDTH = 8;
    parameter DEPTH      = 16;
    parameter ADDR_WIDTH = $clog2(DEPTH);

    // ==========================================================================
    // DUT signals
    // ==========================================================================
    logic                  clk;
    logic                  rst_n;
    logic                  wr_en;
    logic [DATA_WIDTH-1:0] wr_data;
    logic                  full;
    logic                  rd_en;
    logic [DATA_WIDTH-1:0] rd_data;
    logic                  empty;
    logic [ADDR_WIDTH:0]   count;

    // ==========================================================================
    // DUT instantiation
    // ==========================================================================
    sync_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .wr_en(wr_en),
        .wr_data(wr_data),
        .full(full),
        .rd_en(rd_en),
        .rd_data(rd_data),
        .empty(empty),
        .count(count)
    );

    // ==========================================================================
    // Clock generation
    // ==========================================================================
    initial clk = 0;
    always #5 clk = ~clk;  // 100MHz

    // ==========================================================================
    // Test sequence
    // ==========================================================================
    int errors;
    logic [DATA_WIDTH-1:0] expected_data [$];

    initial begin
        $display("=== Sync FIFO Testbench Started ===");
        errors = 0;
        
        // Initialize
        rst_n   = 0;
        wr_en   = 0;
        rd_en   = 0;
        wr_data = 0;
        
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
        
        // Test 1: Check initial state
        $display("Test 1: Initial state");
        assert(empty == 1) else begin $error("FIFO should be empty"); errors++; end
        assert(full == 0)  else begin $error("FIFO should not be full"); errors++; end
        assert(count == 0) else begin $error("Count should be 0"); errors++; end
        
        // Test 2: Write single entry
        $display("Test 2: Single write");
        @(posedge clk);
        wr_en = 1;
        wr_data = 8'hA5;
        expected_data.push_back(8'hA5);
        @(posedge clk);
        wr_en = 0;
        @(posedge clk);
        
        assert(empty == 0) else begin $error("FIFO should not be empty"); errors++; end
        assert(count == 1) else begin $error("Count should be 1"); errors++; end
        
        // Test 3: Read single entry
        $display("Test 3: Single read");
        rd_en = 1;
        @(posedge clk);
        assert(rd_data == expected_data.pop_front()) else begin $error("Read data mismatch"); errors++; end
        rd_en = 0;
        @(posedge clk);
        
        assert(empty == 1) else begin $error("FIFO should be empty"); errors++; end
        
        // Test 4: Fill FIFO completely
        $display("Test 4: Fill FIFO");
        for (int i = 0; i < DEPTH; i++) begin
            wr_en = 1;
            wr_data = i;
            expected_data.push_back(i);
            @(posedge clk);
        end
        wr_en = 0;
        @(posedge clk);
        
        assert(full == 1) else begin $error("FIFO should be full"); errors++; end
        assert(count == DEPTH) else begin $error("Count should equal DEPTH"); errors++; end
        
        // Test 5: Read all entries
        $display("Test 5: Read all entries");
        for (int i = 0; i < DEPTH; i++) begin
            rd_en = 1;
            @(posedge clk);
            assert(rd_data == expected_data.pop_front()) else begin $error("Data mismatch at %0d", i); errors++; end
        end
        rd_en = 0;
        @(posedge clk);
        
        assert(empty == 1) else begin $error("FIFO should be empty"); errors++; end
        
        // Test 6: Simultaneous read/write
        $display("Test 6: Simultaneous read/write");
        // First put some data in
        for (int i = 0; i < DEPTH/2; i++) begin
            wr_en = 1;
            wr_data = i + 100;
            expected_data.push_back(i + 100);
            @(posedge clk);
        end
        wr_en = 0;
        @(posedge clk);
        
        // Now do simultaneous read/write
        for (int i = 0; i < 8; i++) begin
            wr_en = 1;
            rd_en = 1;
            wr_data = i + 200;
            expected_data.push_back(i + 200);
            @(posedge clk);
            assert(rd_data == expected_data.pop_front()) else begin $error("Simultaneous R/W mismatch"); errors++; end
        end
        wr_en = 0;
        rd_en = 0;
        
        // Drain remaining
        while (!empty) begin
            rd_en = 1;
            @(posedge clk);
            if (expected_data.size() > 0)
                assert(rd_data == expected_data.pop_front()) else begin $error("Drain mismatch"); errors++; end
        end
        rd_en = 0;
        
        // Summary
        repeat(5) @(posedge clk);
        $display("=== Test Complete ===");
        if (errors == 0)
            $display("PASSED: All tests passed!");
        else
            $display("FAILED: %0d errors", errors);
        
        $finish;
    end

    // Timeout watchdog
    initial begin
        #100000;
        $error("Timeout!");
        $finish;
    end

endmodule
