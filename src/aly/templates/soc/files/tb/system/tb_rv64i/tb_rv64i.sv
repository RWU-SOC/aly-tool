`timescale 1ns/1ps
import as_pack::*;

module tb_rv64i();
    // Parameters from package
    parameter clk_2_t = 5;

    logic clk_s, rst_s;
    tri [nr_gpios-1:0] gpio_s;
    logic cs_s;

    // Instruction memory (word-addressed array)
    logic [instr_width-1:0] iram_s [0:imemdepth-1];

    // DUT instantiation (expects as_top_mem available in project)
    as_top_mem DUT (
        .clk_i(clk_s),
        .rst_i(rst_s),
        .gpio_io(gpio_s),
        .cs_o(cs_s)
    );

    initial begin
        clk_s = 0;
        rst_s = 1;
        #20 rst_s = 0;

        // Load instructions via plusarg IMEM_FILE
        string memfile = "";
        if ($value$plusargs("IMEM_FILE=%s", memfile)) begin
            $display("Loading IMEM from %s", memfile);
            $readmemh(memfile, iram_s);
        end

        // Wait for DUT to assert chip-select and check gpio
        forever begin
            @(negedge clk_s);
            if (cs_s === 1) begin
                case (gpio_s)
                    1: $display("Test step 1 passed");
                    7: begin
                        $display("Simulation succeeded");
                        $stop;
                    end
                    default: begin
                        $display("Unexpected GPIO: 0x%0h", gpio_s);
                        $stop;
                    end
                endcase
            end
        end
    end

    always #clk_2_t clk_s = ~clk_s;
endmodule
