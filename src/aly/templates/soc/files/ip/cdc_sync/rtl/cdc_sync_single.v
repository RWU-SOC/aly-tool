// CDC Synchronizer (Single Bit) - Verilog
// =============================================================================
// Multi-stage flip-flop synchronizer for clock domain crossing.
// Uses ASYNC_REG attribute for proper synthesis tool handling.
// =============================================================================

module cdc_sync_single #(
    parameter STAGES    = 2,    // Number of sync stages
    parameter RESET_VAL = 1'b0  // Reset value
)(
    input  wire clk_dst,    // Destination clock
    input  wire rst_dst_n,  // Destination reset (active low)
    input  wire data_src,   // Source domain data
    output wire data_dst    // Synchronized output
);

    // Synchronizer chain with ASYNC_REG attribute
    (* ASYNC_REG = "TRUE" *) reg [STAGES-1:0] sync_chain;
    
    integer i;

    always @(posedge clk_dst or negedge rst_dst_n) begin
        if (!rst_dst_n) begin
            sync_chain <= {STAGES{RESET_VAL}};
        end else begin
            sync_chain[0] <= data_src;
            for (i = 1; i < STAGES; i = i + 1) begin
                sync_chain[i] <= sync_chain[i-1];
            end
        end
    end

    assign data_dst = sync_chain[STAGES-1];

endmodule
