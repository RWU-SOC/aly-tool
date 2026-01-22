// CDC Synchronizer (Single Bit) - SystemVerilog
// =============================================================================
// Multi-stage flip-flop synchronizer for clock domain crossing.
// Uses ASYNC_REG attribute for proper synthesis tool handling.
// =============================================================================

module cdc_sync_single #(
    parameter int STAGES    = 2,     // Number of sync stages
    parameter bit RESET_VAL = 1'b0   // Reset value
)(
    input  logic clk_dst,    // Destination clock
    input  logic rst_dst_n,  // Destination reset (active low)
    input  logic data_src,   // Source domain data
    output logic data_dst    // Synchronized output
);

    // Synchronizer chain with ASYNC_REG attribute
    (* ASYNC_REG = "TRUE" *) logic [STAGES-1:0] sync_chain;

    always_ff @(posedge clk_dst or negedge rst_dst_n) begin
        if (!rst_dst_n) begin
            sync_chain <= {STAGES{RESET_VAL}};
        end else begin
            sync_chain <= {sync_chain[STAGES-2:0], data_src};
        end
    end

    assign data_dst = sync_chain[STAGES-1];

endmodule
