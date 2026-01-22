// Testbench for Round-Robin Arbiter - Verilog
// =============================================================================

`timescale 1ns/1ps

module tb_rr_arbiter;

    // ==========================================================================
    // Parameters
    // ==========================================================================
    parameter NUM_REQ   = 4;
    parameter REQ_WIDTH = 2;

    // ==========================================================================
    // DUT signals
    // ==========================================================================
    reg                clk;
    reg                rst_n;
    reg  [NUM_REQ-1:0] req;
    wire [NUM_REQ-1:0] grant;
    reg                enable;
    wire               valid;

    // Test variables
    integer errors;
    integer grant_count [0:NUM_REQ-1];
    integer i, cycle;

    // ==========================================================================
    // DUT instantiation
    // ==========================================================================
    rr_arbiter #(
        .NUM_REQ(NUM_REQ),
        .REQ_WIDTH(REQ_WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .req(req),
        .grant(grant),
        .enable(enable),
        .valid(valid)
    );

    // ==========================================================================
    // Clock generation
    // ==========================================================================
    initial clk = 0;
    always #5 clk = ~clk;  // 100MHz

    // ==========================================================================
    // Helper function: check one-hot
    // ==========================================================================
    function check_one_hot;
        input [NUM_REQ-1:0] g;
        integer cnt;
        integer j;
        begin
            cnt = 0;
            for (j = 0; j < NUM_REQ; j = j + 1) begin
                if (g[j]) cnt = cnt + 1;
            end
            check_one_hot = (cnt <= 1);
        end
    endfunction

    // ==========================================================================
    // Test sequence
    // ==========================================================================
    initial begin
        $display("=== Round-Robin Arbiter Testbench ===");
        errors = 0;
        for (i = 0; i < NUM_REQ; i = i + 1) grant_count[i] = 0;
        
        // Initialize
        rst_n  = 0;
        req    = 0;
        enable = 0;
        
        repeat(5) @(posedge clk);
        rst_n = 1;
        @(posedge clk);
        
        // Test 1: No requests
        $display("Test 1: No requests");
        enable = 1;
        req = 0;
        @(posedge clk);
        if (valid != 0) begin $display("ERROR: Valid should be 0 with no requests"); errors = errors + 1; end
        if (grant != 0) begin $display("ERROR: Grant should be 0"); errors = errors + 1; end
        
        // Test 2: Single request
        $display("Test 2: Single request");
        req = 4'b0010;  // Request from port 1
        @(posedge clk);
        if (valid != 1) begin $display("ERROR: Valid should be 1"); errors = errors + 1; end
        if (grant != 4'b0010) begin $display("ERROR: Grant should be on port 1"); errors = errors + 1; end
        if (!check_one_hot(grant)) begin $display("ERROR: Grant not one-hot"); errors = errors + 1; end
        
        // Test 3: Multiple requests - round robin
        $display("Test 3: Round-robin behavior");
        req = 4'b1111;  // All requests active
        
        // Should cycle through all ports
        for (cycle = 0; cycle < 8; cycle = cycle + 1) begin
            @(posedge clk);
            if (valid != 1) begin $display("ERROR: Valid should be 1"); errors = errors + 1; end
            if (!check_one_hot(grant)) begin $display("ERROR: Grant not one-hot"); errors = errors + 1; end
            
            // Count grants
            for (i = 0; i < NUM_REQ; i = i + 1) begin
                if (grant[i]) grant_count[i] = grant_count[i] + 1;
            end
        end
        
        // Print grant counts
        for (i = 0; i < NUM_REQ; i = i + 1) begin
            $display("  Port %0d: %0d grants", i, grant_count[i]);
        end
        
        // Test 4: Enable control
        $display("Test 4: Enable control");
        enable = 0;
        req = 4'b1111;
        @(posedge clk);
        if (valid != 0) begin $display("ERROR: Valid should be 0 when disabled"); errors = errors + 1; end
        if (grant != 0) begin $display("ERROR: Grant should be 0 when disabled"); errors = errors + 1; end
        
        enable = 1;
        @(posedge clk);
        if (valid != 1) begin $display("ERROR: Valid should be 1 when enabled"); errors = errors + 1; end
        
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
        #50000;
        $display("ERROR: Timeout!");
        $finish;
    end

endmodule
