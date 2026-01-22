`timescale 1ns/1ps

module tb_memory_instr;
    // Instruction memory fetch testbench
    parameter int IMEM_WIDTH = 32;
    parameter int IMEM_DEPTH = 8192;

    string imem_file = "";

    logic clk, rst_n;
    logic [31:0] pc;
    logic [IMEM_WIDTH-1:0] instr;

    // Simple ROM array for instruction memory
    logic [IMEM_WIDTH-1:0] imem [0:IMEM_DEPTH-1];

    initial begin
        clk = 0;
        rst_n = 0;
        #20 rst_n = 1;

        if ($value$plusargs("IMEM_FILE=%s", imem_file)) begin
            $display("Loading IMEM from %s", imem_file);
            $readmemh(imem_file, imem);
        end

        pc = 0;
        repeat(16) begin
            @(posedge clk);
            $display("PC=%08h INSTR=%08h", pc, imem[pc>>2]);
            pc = pc + 4;
        end

        $finish;
    end

    // Clock
    always #5 clk = ~clk;
endmodule
