# Arty A7-100T Constraint File
# Simple test constraints for counter IP

# Clock constraint (100 MHz)
create_clock -period 10.0 -name clk [get_ports clk]

# I/O constraints (example pins)
set_property PACKAGE_PIN E3 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]

set_property PACKAGE_PIN C2 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
