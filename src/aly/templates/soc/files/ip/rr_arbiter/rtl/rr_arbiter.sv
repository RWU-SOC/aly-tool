// Round-Robin Arbiter - SystemVerilog
// =============================================================================
// A fair round-robin arbiter with configurable number of request inputs.
// Grants are issued in round-robin order, with priority rotating after each grant.
// =============================================================================

module rr_arbiter #(
    parameter int NUM_REQ = 4
)(
    input  logic               clk,
    input  logic               rst_n,
    
    // Request/Grant interface
    input  logic [NUM_REQ-1:0] req,
    output logic [NUM_REQ-1:0] grant,
    
    // Control
    input  logic               enable,
    output logic               valid
);

    // ==========================================================================
    // Internal signals
    // ==========================================================================
    logic [$clog2(NUM_REQ)-1:0] last_grant;
    logic [NUM_REQ-1:0]         mask;
    logic [NUM_REQ-1:0]         masked_req;
    logic [NUM_REQ-1:0]         masked_grant;
    logic [NUM_REQ-1:0]         unmasked_grant;
    logic                       masked_valid;
    
    // ==========================================================================
    // Generate mask based on last grant
    // ==========================================================================
    always_comb begin
        mask = '0;
        for (int i = 0; i < NUM_REQ; i++) begin
            if (i > last_grant) begin
                mask[i] = 1'b1;
            end
        end
    end
    
    // Masked requests
    assign masked_req = req & mask;
    
    // ==========================================================================
    // Priority encoder for masked requests
    // ==========================================================================
    always_comb begin
        masked_grant = '0;
        for (int i = 0; i < NUM_REQ; i++) begin
            if (masked_req[i] && masked_grant == '0) begin
                masked_grant[i] = 1'b1;
            end
        end
    end
    
    assign masked_valid = |masked_req;
    
    // ==========================================================================
    // Priority encoder for unmasked requests (wrap-around)
    // ==========================================================================
    always_comb begin
        unmasked_grant = '0;
        for (int i = 0; i < NUM_REQ; i++) begin
            if (req[i] && unmasked_grant == '0) begin
                unmasked_grant[i] = 1'b1;
            end
        end
    end
    
    // ==========================================================================
    // Select grant and update state
    // ==========================================================================
    assign grant = enable ? (masked_valid ? masked_grant : unmasked_grant) : '0;
    assign valid = enable && |req;
    
    // Update last grant
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            last_grant <= '0;
        end else if (valid) begin
            for (int i = 0; i < NUM_REQ; i++) begin
                if (grant[i]) begin
                    last_grant <= i[$clog2(NUM_REQ)-1:0];
                end
            end
        end
    end

endmodule
