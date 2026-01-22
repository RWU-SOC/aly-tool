# Vivado Synthesis Script
# =============================================================================
# Run with: vivado -mode batch -source synth.tcl -tclargs <part> <top>
# =============================================================================

# Get arguments
set part [lindex $argv 0]
set top [lindex $argv 1]

if {$part eq "" || $top eq ""} {
    puts "Usage: vivado -mode batch -source synth.tcl -tclargs <part> <top>"
    puts "  part: FPGA part number (e.g., xc7a100tcsg324-1)"
    puts "  top:  Top module name"
    exit 1
}

# Create project in memory
create_project -in_memory -part $part

# Set project properties
set_property target_language Verilog [current_project]
set_property default_lib work [current_project]

# Create output directories
file mkdir reports
file mkdir outputs

# Read design sources
puts "Reading RTL sources..."
read_verilog -sv [glob -nocomplain rtl/pkg/*.sv]
read_verilog -sv [glob -nocomplain rtl/lib/*.sv]
read_verilog -sv [glob -nocomplain rtl/mem/*.sv]
read_verilog -sv [glob -nocomplain rtl/periph/**/*.sv]
read_verilog -sv [glob -nocomplain rtl/core/**/*.sv]
read_verilog -sv [glob -nocomplain rtl/top/*.sv]

# Read IP sources
read_verilog -sv [glob -nocomplain ip/*/rtl/*.sv]

# Read constraints
read_xdc [glob -nocomplain synth/constraints/*.xdc]

# Run synthesis
puts "Running synthesis for $top on $part..."
synth_design -part $part -top $top -flatten_hierarchy rebuilt

# Generate post-synthesis reports
puts "Generating reports..."
report_utilization -file reports/post_synth_utilization.rpt
report_timing_summary -delay_type min_max -file reports/post_synth_timing.rpt
report_power -file reports/post_synth_power.rpt

# Write checkpoint
write_checkpoint -force outputs/post_synth.dcp

# Run implementation
puts "Running implementation..."
opt_design
place_design
phys_opt_design
route_design

# Generate post-implementation reports
report_utilization -file reports/post_impl_utilization.rpt
report_timing_summary -delay_type min_max -file reports/post_impl_timing.rpt
report_power -file reports/post_impl_power.rpt

# Write bitstream
puts "Generating bitstream..."
write_bitstream -force outputs/${top}.bit

# Write checkpoint
write_checkpoint -force outputs/post_impl.dcp

puts "Synthesis complete!"
puts "  Bitstream: outputs/${top}.bit"
puts "  Reports:   reports/"
