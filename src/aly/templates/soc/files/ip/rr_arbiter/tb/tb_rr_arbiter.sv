// Testbench for Round-Robin Arbiter - SystemVerilog
// =============================================================================

`timescale 1ns/1ps

module tb_rr_arbiter;

    // ==========================================================================
    // Parameters
    // ==========================================================================
    parameter NUM_REQ   = 4;

    // ==========================================================================
    // DUT signals
    // ==========================================================================
    logic               clk;
    logic               rst_n;
    logic [NUM_REQ-1:0] req;
    logic [NUM_REQ-1:0] grant;
    logic               enable;
    logic               valid;

    // ==========================================================================
    // DUT instantiation
    // ==========================================================================
    rr_arbiter #(
        .NUM_REQ(NUM_REQ)
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
    // Test sequence
    // ==========================================================================
    int errors;
    int grant_count [NUM_REQ];

    // Helper function to check one-hot grant
    function automatic logic check_one_hot(logic [NUM_REQ-1:0] g);
        int count = 0;
        for (int i = 0; i < NUM_REQ; i++) begin
            if (g[i]) count++;
        end
        return (count <= 1);
    endfunction

    initial begin
        $display("=== Round-Robin Arbiter Testbench ===");
        errors = 0;
        for (int i = 0; i < NUM_REQ; i++) grant_count[i] = 0;
        
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
        assert(valid == 0) else begin $error("Valid should be 0 with no requests"); errors++; end
        assert(grant == 0) else begin $error("Grant should be 0"); errors++; end
        
        // Test 2: Single request
        $display("Test 2: Single request");
        req = 4'b0010;  // Request from port 1
        @(posedge clk);
        assert(valid == 1) else begin $error("Valid should be 1"); errors++; end
        assert(grant == 4'b0010) else begin $error("Grant should be on port 1"); errors++; end
        assert(check_one_hot(grant)) else begin $error("Grant not one-hot"); errors++; end
        
        // Test 3: Multiple requests - round robin
        $display("Test 3: Round-robin behavior");
        req = 4'b1111;  // All requests active
        
        // Should cycle through all ports
        for (int cycle = 0; cycle < 8; cycle++) begin
            @(posedge clk);
            assert(valid == 1) else begin $error("Valid should be 1"); errors++; end
            assert(check_one_hot(grant)) else begin $error("Grant not one-hot"); errors++; end
            
            // Count grants
            for (int i = 0; i < NUM_REQ; i++) begin
                if (grant[i]) grant_count[i]++;
            end
        end
        
        // Verify fairness (each port should have ~2 grants in 8 cycles)
        for (int i = 0; i < NUM_REQ; i++) begin
            $display("  Port %0d: %0d grants", i, grant_count[i]);
            if (grant_count[i] < 1 || grant_count[i] > 3) begin
                $error("Unfair arbitration for port %0d", i);
                errors++;
            end
        end
        
        // Test 4: Enable control
        $display("Test 4: Enable control");
        enable = 0;
        req = 4'b1111;
        @(posedge clk);
        assert(valid == 0) else begin $error("Valid should be 0 when disabled"); errors++; end
        assert(grant == 0) else begin $error("Grant should be 0 when disabled"); errors++; end
        
        enable = 1;
        @(posedge clk);
        assert(valid == 1) else begin $error("Valid should be 1 when enabled"); errors++; end
        
        // Test 5: Changing requests
        $display("Test 5: Changing requests");
        req = 4'b1010;  // Ports 1 and 3
        @(posedge clk);
        assert(grant == 4'b0010 || grant == 4'b1000) 
            else begin $error("Grant should be on port 1 or 3"); errors++; end
        
        req = 4'b0101;  // Ports 0 and 2
        @(posedge clk);
        assert(grant == 4'b0001 || grant == 4'b0100) 
            else begin $error("Grant should be on port 0 or 2"); errors++; end
        
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
        $error("Timeout!");
        $finish;
    end

endmodule
