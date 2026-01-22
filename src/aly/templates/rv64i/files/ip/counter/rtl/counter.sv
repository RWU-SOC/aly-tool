// Simple Parameterized Counter
// Author: ALY IP Generator
// License: Apache-2.0

module counter #(
    parameter int WIDTH = 32,
    parameter int MAX_VALUE = 0  // 0 = no limit (wrap at 2^WIDTH)
)(
    input  logic             clk,
    input  logic             rst_n,
    input  logic             enable,
    input  logic             clear,
    input  logic             load,
    input  logic [WIDTH-1:0] load_value,
    output logic [WIDTH-1:0] count,
    output logic             overflow
);

    logic [WIDTH-1:0] max_count;

    // Determine max count value
    assign max_count = (MAX_VALUE == 0) ? {WIDTH{1'b1}} : WIDTH'(MAX_VALUE);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= '0;
            overflow <= 1'b0;
        end else if (clear) begin
            count <= '0;
            overflow <= 1'b0;
        end else if (load) begin
            count <= load_value;
            overflow <= 1'b0;
        end else if (enable) begin
            if (count >= max_count) begin
                count <= '0;
                overflow <= 1'b1;
            end else begin
                count <= count + 1'b1;
                overflow <= 1'b0;
            end
        end else begin
            overflow <= 1'b0;
        end
    end

endmodule
