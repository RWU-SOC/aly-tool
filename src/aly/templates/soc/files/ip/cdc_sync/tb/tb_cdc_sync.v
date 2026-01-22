// Testbench for CDC Synchronizers - Verilog
// =============================================================================

`timescale 1ns/1ps

module tb_cdc_sync;

    // ==========================================================================
    // Parameters
    // ==========================================================================
    parameter STAGES = 2;
    parameter WIDTH  = 8;

    // Clock periods
    parameter SRC_CLK_PERIOD = 10;
    parameter DST_CLK_PERIOD = 7;

    // ==========================================================================
    // Signals
    // ==========================================================================
    reg              clk_src;
    reg              clk_dst;
    reg              rst_n;
    reg              data_src_single;
    wire             data_dst_single;
    reg  [WIDTH-1:0] data_src_bus;
    wire [WIDTH-1:0] data_dst_bus;

    integer errors;
    integer i;

    // ==========================================================================
    // DUT instantiations
    // ==========================================================================
    cdc_sync_single #(
        .STAGES(STAGES),
        .RESET_VAL(1'b0)
    ) dut_single (
        .clk_dst(clk_dst),
        .rst_dst_n(rst_n),
        .data_src(data_src_single),
        .data_dst(data_dst_single)
    );

    cdc_sync_bus #(
        .WIDTH(WIDTH),
        .STAGES(STAGES),
        .RESET_VAL(1'b0)
    ) dut_bus (
        .clk_src(clk_src),
        .rst_src_n(rst_n),
        .data_src(data_src_bus),
        .clk_dst(clk_dst),
        .rst_dst_n(rst_n),
        .data_dst(data_dst_bus)
    );

    // ==========================================================================
    // Clock generation
    // ==========================================================================
    initial clk_src = 0;
    always #(SRC_CLK_PERIOD/2) clk_src = ~clk_src;

    initial clk_dst = 0;
    always #(DST_CLK_PERIOD/2) clk_dst = ~clk_dst;

    // ==========================================================================
    // Test sequence
    // ==========================================================================
    initial begin
        $display("=== CDC Synchronizer Testbench ===");
        errors = 0;
        
        // Initialize
        rst_n = 0;
        data_src_single = 0;
        data_src_bus = 0;
        
        // Reset
        repeat(10) @(posedge clk_dst);
        rst_n = 1;
        repeat(5) @(posedge clk_dst);

        // Test 1: Single-bit synchronizer
        $display("Test 1: Single-bit synchronizer");
        
        @(posedge clk_src);
        data_src_single = 1;
        repeat(STAGES + 2) @(posedge clk_dst);
        
        if (data_dst_single != 1) begin 
            $display("ERROR: Single-bit sync failed: expected 1, got %b", data_dst_single); 
            errors = errors + 1; 
        end
        
        @(posedge clk_src);
        data_src_single = 0;
        repeat(STAGES + 2) @(posedge clk_dst);
        
        if (data_dst_single != 0) begin 
            $display("ERROR: Single-bit sync failed: expected 0, got %b", data_dst_single); 
            errors = errors + 1; 
        end

        // Test 2: Bus synchronizer
        $display("Test 2: Bus synchronizer");
        
        @(posedge clk_src);
        data_src_bus = 8'hA5;
        repeat(STAGES + 5) @(posedge clk_dst);
        
        if (data_dst_bus != 8'hA5) begin 
            $display("ERROR: Bus sync failed: expected A5, got %02h", data_dst_bus); 
            errors = errors + 1; 
        end

        // Test 3: Toggle test
        $display("Test 3: Toggle test");
        
        for (i = 0; i < 10; i = i + 1) begin
            @(posedge clk_src);
            data_src_single = ~data_src_single;
            repeat(STAGES + 1) @(posedge clk_dst);
        end

        // Test 4: Counter pattern
        $display("Test 4: Counter pattern");
        
        for (i = 0; i < 32; i = i + 1) begin
            @(posedge clk_src);
            data_src_bus = i;
            repeat(2) @(posedge clk_dst);
        end
        
        @(posedge clk_src);
        data_src_bus = 8'h55;
        repeat(STAGES + 5) @(posedge clk_dst);
        
        if (data_dst_bus != 8'h55) begin 
            $display("ERROR: Counter test failed: expected 55, got %02h", data_dst_bus); 
            errors = errors + 1; 
        end

        // Summary
        repeat(10) @(posedge clk_dst);
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
