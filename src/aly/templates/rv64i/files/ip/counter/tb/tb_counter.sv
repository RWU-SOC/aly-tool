`timescale 1ns/1ps

module tb_counter();
    parameter WIDTH = 8;
    parameter MAX_VALUE = 10;

    logic clk;
    logic rst_n;
    logic enable;
    logic clear;
    logic load;
    logic [WIDTH-1:0] load_value;
    logic [WIDTH-1:0] count;
    logic overflow;

    // Instantiate DUT
    counter #(
        .WIDTH(WIDTH),
        .MAX_VALUE(MAX_VALUE)
    ) DUT (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .clear(clear),
        .load(load),
        .load_value(load_value),
        .count(count),
        .overflow(overflow)
    );

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

    // Stimulus
    initial begin
        rst_n = 0;
        enable = 0;
        clear = 0;
        load = 0;
        load_value = 0;
        #20;
        rst_n = 1;
        #10;
        // Test clear
        clear = 1;
        #10;
        clear = 0;
        // Test load
        load_value = 5;
        load = 1;
        #10;
        load = 0;
        // Test count up
        enable = 1;
        repeat (15) #10;
        enable = 0;
        // Test overflow
        #20;
        $stop;
    end
endmodule
