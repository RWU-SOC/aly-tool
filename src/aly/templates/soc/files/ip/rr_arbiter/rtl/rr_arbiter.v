// Round-Robin Arbiter - Verilog
// =============================================================================
// A fair round-robin arbiter with configurable number of request inputs.
// Grants are issued in round-robin order, with priority rotating after each grant.
// =============================================================================

module rr_arbiter #(
    parameter NUM_REQ   = 4,
    parameter REQ_WIDTH = 2  // log2(NUM_REQ)
)(
    input  wire               clk,
    input  wire               rst_n,
    
    // Request/Grant interface
    input  wire [NUM_REQ-1:0] req,
    output reg  [NUM_REQ-1:0] grant,
    
    // Control
    input  wire               enable,
    output wire               valid
);

    // ==========================================================================
    // Internal signals
    // ==========================================================================
    reg  [REQ_WIDTH-1:0]  last_grant;
    reg  [NUM_REQ-1:0]    mask;
    wire [NUM_REQ-1:0]    masked_req;
    reg  [NUM_REQ-1:0]    masked_grant;
    reg  [NUM_REQ-1:0]    unmasked_grant;
    wire                  masked_valid;
    
    integer i;
    
    // ==========================================================================
    // Generate mask based on last grant
    // ==========================================================================
    always @(*) begin
        mask = {NUM_REQ{1'b0}};
        for (i = 0; i < NUM_REQ; i = i + 1) begin
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
    always @(*) begin
        masked_grant = {NUM_REQ{1'b0}};
        for (i = 0; i < NUM_REQ; i = i + 1) begin
            if (masked_req[i] && masked_grant == {NUM_REQ{1'b0}}) begin
                masked_grant[i] = 1'b1;
            end
        end
    end
    
    assign masked_valid = |masked_req;
    
    // ==========================================================================
    // Priority encoder for unmasked requests (wrap-around)
    // ==========================================================================
    always @(*) begin
        unmasked_grant = {NUM_REQ{1'b0}};
        for (i = 0; i < NUM_REQ; i = i + 1) begin
            if (req[i] && unmasked_grant == {NUM_REQ{1'b0}}) begin
                unmasked_grant[i] = 1'b1;
            end
        end
    end
    
    // ==========================================================================
    // Select grant
    // ==========================================================================
    always @(*) begin
        if (enable) begin
            grant = masked_valid ? masked_grant : unmasked_grant;
        end else begin
            grant = {NUM_REQ{1'b0}};
        end
    end
    
    assign valid = enable && (|req);
    
    // ==========================================================================
    // Update last grant
    // ==========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            last_grant <= {REQ_WIDTH{1'b0}};
        end else if (valid) begin
            for (i = 0; i < NUM_REQ; i = i + 1) begin
                if (grant[i]) begin
                    last_grant <= i[REQ_WIDTH-1:0];
                end
            end
        end
    end

endmodule
