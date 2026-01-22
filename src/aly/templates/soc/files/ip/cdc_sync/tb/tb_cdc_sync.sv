// Testbench for CDC Synchronizers - SystemVerilog
// =============================================================================

`timescale 1ns/1ps

module tb_cdc_sync;

    // ==========================================================================
    // Parameters
    // ==========================================================================
    parameter STAGES = 2;
    parameter WIDTH  = 8;

    // ==========================================================================
    // Clock periods (different domains)
    // ==========================================================================
    parameter SRC_CLK_PERIOD = 10;  // 100MHz source
    parameter DST_CLK_PERIOD = 7;   // ~143MHz destination

    // ==========================================================================
    // Signals for single-bit synchronizer
    // ==========================================================================
    logic clk_src_single;
    logic clk_dst_single;
    logic rst_n;
    logic data_src_single;
    logic data_dst_single;

    // ==========================================================================
    // Signals for bus synchronizer
    // ==========================================================================
    logic              clk_src_bus;
    logic              clk_dst_bus;
    logic [WIDTH-1:0]  data_src_bus;
    logic [WIDTH-1:0]  data_dst_bus;

    // ==========================================================================
    // DUT instantiations
    // ==========================================================================
    cdc_sync_single #(
        .STAGES(STAGES),
        .RESET_VAL(1'b0)
    ) dut_single (
        .clk_dst(clk_dst_single),
        .rst_dst_n(rst_n),
        .data_src(data_src_single),
        .data_dst(data_dst_single)
    );

    cdc_sync_bus #(
        .WIDTH(WIDTH),
        .STAGES(STAGES),
        .RESET_VAL(1'b0)
    ) dut_bus (
        .clk_src(clk_src_bus),
        .rst_src_n(rst_n),
        .data_src(data_src_bus),
        .clk_dst(clk_dst_bus),
        .rst_dst_n(rst_n),
        .data_dst(data_dst_bus)
    );

    // ==========================================================================
    // Clock generation
    // ==========================================================================
    initial clk_src_single = 0;
    always #(SRC_CLK_PERIOD/2) clk_src_single = ~clk_src_single;

    initial clk_dst_single = 0;
    always #(DST_CLK_PERIOD/2) clk_dst_single = ~clk_dst_single;

    assign clk_src_bus = clk_src_single;
    assign clk_dst_bus = clk_dst_single;

    // ==========================================================================
    // Test sequence
    // ==========================================================================
    int errors;

    initial begin
        $display("=== CDC Synchronizer Testbench ===");
        errors = 0;
        
        // Initialize
        rst_n = 0;
        data_src_single = 0;
        data_src_bus = 0;
        
        // Reset
        repeat(10) @(posedge clk_dst_single);
        rst_n = 1;
        repeat(5) @(posedge clk_dst_single);

        // =======================================================================
        // Test 1: Single-bit synchronizer basic operation
        // =======================================================================
        $display("Test 1: Single-bit synchronizer");
        
        // Assert signal in source domain
        @(posedge clk_src_single);
        data_src_single = 1;
        
        // Wait for synchronization (STAGES + margin cycles)
        repeat(STAGES + 2) @(posedge clk_dst_single);
        
        // Check synchronized output
        assert(data_dst_single == 1) 
            else begin $error("Single-bit sync failed: expected 1, got %b", data_dst_single); errors++; end
        
        // Deassert signal
        @(posedge clk_src_single);
        data_src_single = 0;
        repeat(STAGES + 2) @(posedge clk_dst_single);
        
        assert(data_dst_single == 0) 
            else begin $error("Single-bit sync failed: expected 0, got %b", data_dst_single); errors++; end

        // =======================================================================
        // Test 2: Bus synchronizer basic operation
        // =======================================================================
        $display("Test 2: Bus synchronizer");
        
        // Test several values
        for (int val = 0; val < 16; val++) begin
            @(posedge clk_src_bus);
            data_src_bus = val;
            
            // Wait for synchronization (need extra cycles for gray code)
            repeat(STAGES + 4) @(posedge clk_dst_bus);
            
            // Note: Due to gray-code, we need stable input for accurate sync
        end
        
        // Hold steady value and verify
        @(posedge clk_src_bus);
        data_src_bus = 8'hA5;
        repeat(STAGES + 5) @(posedge clk_dst_bus);
        
        assert(data_dst_bus == 8'hA5) 
            else begin $error("Bus sync failed: expected A5, got %02h", data_dst_bus); errors++; end

        // =======================================================================
        // Test 3: Toggle test for single-bit
        // =======================================================================
        $display("Test 3: Toggle test");
        
        for (int i = 0; i < 10; i++) begin
            @(posedge clk_src_single);
            data_src_single = ~data_src_single;
            repeat(STAGES + 1) @(posedge clk_dst_single);
        end

        // =======================================================================
        // Test 4: Counter pattern on bus
        // =======================================================================
        $display("Test 4: Counter pattern");
        
        for (int i = 0; i < 32; i++) begin
            @(posedge clk_src_bus);
            data_src_bus = i;
            repeat(2) @(posedge clk_dst_bus);
        end
        
        // Hold and verify final value
        @(posedge clk_src_bus);
        data_src_bus = 8'h55;
        repeat(STAGES + 5) @(posedge clk_dst_bus);
        
        assert(data_dst_bus == 8'h55) 
            else begin $error("Counter test failed: expected 55, got %02h", data_dst_bus); errors++; end

        // =======================================================================
        // Summary
        // =======================================================================
        repeat(10) @(posedge clk_dst_single);
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
