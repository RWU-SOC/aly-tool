// Testbench for Synchronous FIFO - Verilog
// =============================================================================

`timescale 1ns/1ps

module tb_sync_fifo;

    // ==========================================================================
    // Parameters
    // ==========================================================================
    parameter DATA_WIDTH = 8;
    parameter DEPTH      = 16;
    parameter ADDR_WIDTH = 4;  // log2(DEPTH)

    // ==========================================================================
    // DUT signals
    // ==========================================================================
    reg                   clk;
    reg                   rst_n;
    reg                   wr_en;
    reg  [DATA_WIDTH-1:0] wr_data;
    wire                  full;
    reg                   rd_en;
    wire [DATA_WIDTH-1:0] rd_data;
    wire                  empty;
    wire [ADDR_WIDTH:0]   count;

    // Test variables
    integer errors;
    integer i;
    reg [DATA_WIDTH-1:0] expected_fifo [0:DEPTH-1];
    integer expected_head;
    integer expected_tail;
    integer expected_count;

    // ==========================================================================
    // DUT instantiation
    // ==========================================================================
    sync_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH),
        .ADDR_WIDTH(ADDR_WIDTH)
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
    // Helper tasks
    // ==========================================================================
    task expect_push;
        input [DATA_WIDTH-1:0] data;
        begin
            expected_fifo[expected_tail] = data;
            expected_tail = (expected_tail + 1) % DEPTH;
            expected_count = expected_count + 1;
        end
    endtask

    task expect_pop;
        begin
            expected_head = (expected_head + 1) % DEPTH;
            expected_count = expected_count - 1;
        end
    endtask

    // ==========================================================================
    // Test sequence
    // ==========================================================================
    initial begin
        $display("=== Sync FIFO Testbench Started ===");
        errors = 0;
        expected_head = 0;
        expected_tail = 0;
        expected_count = 0;
        
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
        if (empty != 1) begin $display("ERROR: FIFO should be empty"); errors = errors + 1; end
        if (full != 0)  begin $display("ERROR: FIFO should not be full"); errors = errors + 1; end
        if (count != 0) begin $display("ERROR: Count should be 0"); errors = errors + 1; end
        
        // Test 2: Write single entry
        $display("Test 2: Single write");
        @(posedge clk);
        wr_en = 1;
        wr_data = 8'hA5;
        expect_push(8'hA5);
        @(posedge clk);
        wr_en = 0;
        @(posedge clk);
        
        if (empty != 0) begin $display("ERROR: FIFO should not be empty"); errors = errors + 1; end
        if (count != 1) begin $display("ERROR: Count should be 1"); errors = errors + 1; end
        
        // Test 3: Read single entry
        $display("Test 3: Single read");
        rd_en = 1;
        @(posedge clk);
        if (rd_data != expected_fifo[expected_head]) begin 
            $display("ERROR: Read data mismatch, got %h expected %h", rd_data, expected_fifo[expected_head]); 
            errors = errors + 1; 
        end
        expect_pop();
        rd_en = 0;
        @(posedge clk);
        
        if (empty != 1) begin $display("ERROR: FIFO should be empty"); errors = errors + 1; end
        
        // Test 4: Fill FIFO completely
        $display("Test 4: Fill FIFO");
        for (i = 0; i < DEPTH; i = i + 1) begin
            wr_en = 1;
            wr_data = i;
            expect_push(i);
            @(posedge clk);
        end
        wr_en = 0;
        @(posedge clk);
        
        if (full != 1) begin $display("ERROR: FIFO should be full"); errors = errors + 1; end
        if (count != DEPTH) begin $display("ERROR: Count should equal DEPTH"); errors = errors + 1; end
        
        // Test 5: Read all entries
        $display("Test 5: Read all entries");
        for (i = 0; i < DEPTH; i = i + 1) begin
            rd_en = 1;
            @(posedge clk);
            if (rd_data != expected_fifo[expected_head]) begin 
                $display("ERROR: Data mismatch at %0d", i); 
                errors = errors + 1; 
            end
            expect_pop();
        end
        rd_en = 0;
        @(posedge clk);
        
        if (empty != 1) begin $display("ERROR: FIFO should be empty"); errors = errors + 1; end
        
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
        $display("ERROR: Timeout!");
        $finish;
    end

endmodule
