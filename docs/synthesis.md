# Synthesis Guide

This guide covers RTL synthesis with ALY, including FPGA synthesis with Vivado and ASIC synthesis with Yosys.

## Quick Start

```bash
# FPGA synthesis with Vivado
aly synth --module cpu --tool vivado --part xc7a100tcsg324-1

# Generic synthesis with Yosys
aly synth --module uart --tool yosys --part generic

# ASIC synthesis with cell library
aly synth --module core --tool yosys --part sky130
```

## Configuration

Synthesis is configured in `.aly/synth.yaml`. Here's a complete example:

```yaml
# Default synthesis tool
default_tool: yosys
build_dir: build/synth

# Cell libraries for ASIC synthesis
libraries:
  sky130_hd:
    liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib
    verilog: libs/sky130_fd_sc_hd.v
    lef: libs/sky130_fd_sc_hd.lef
    description: Sky130 HD standard cells

# Tool configurations
tools:
  yosys:
    bin: yosys
    tech: generic

  vivado:
    bin: vivado
    threads: 8

# Synthesis targets
targets:
  arty_a7:
    tool: vivado
    part: xc7a100tcsg324-1
    top: fpga_top
    constraints:
      - constraints/arty_a7.xdc

  sky130:
    tool: yosys
    tech: sky130
    library: sky130_hd
    top: chip_top
```

## ASIC Synthesis with Cell Libraries

### What is a Liberty File?

A Liberty file (`.lib`) describes the timing, power, and area characteristics of standard cells in a technology library. It's essential for ASIC synthesis to map your RTL to actual silicon cells.

### Yosys ASIC Flow

When you specify a liberty file, ALY runs the following Yosys flow:

```
read_verilog -sv <sources>     # Read RTL
hierarchy -check -top <top>    # Elaborate hierarchy
proc; opt; fsm; opt            # High-level synthesis
memory; opt                    # Memory inference
techmap; opt                   # Map to generic cells
dfflibmap -liberty <lib>       # Map flip-flops to cell library
abc -liberty <lib>             # Map logic to cell library
clean                          # Cleanup
write_verilog synth.v          # Output synthesized netlist
```

### Configuration for ASIC

1. **Define the cell library:**

```yaml
libraries:
  sky130_hd:
    liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib
    verilog: libs/sky130_fd_sc_hd.v   # Optional: for simulation
    lef: libs/sky130_fd_sc_hd.lef     # Optional: for place & route
    description: Sky130 HD standard cells (typical corner)
```

2. **Configure Yosys to use it:**

```yaml
tools:
  yosys:
    bin: yosys
    liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib
```

Or define a target that references the library:

```yaml
targets:
  sky130_asic:
    tool: yosys
    tech: sky130
    library: sky130_hd
    top: chip_top
```

3. **Run synthesis:**

```bash
aly synth --module cpu --tool yosys --part sky130
```

## Where to Get Cell Libraries

### Sky130 (SkyWater 130nm)

Open-source PDK from Google/SkyWater:

```bash
# Clone the PDK
git clone https://github.com/google/skywater-pdk

# Liberty files are in:
# skywater-pdk/libraries/sky130_fd_sc_hd/latest/timing/
# sky130_fd_sc_hd__tt_025C_1v80.lib  (typical corner)
# sky130_fd_sc_hd__ff_n40C_1v95.lib  (fast corner)
# sky130_fd_sc_hd__ss_100C_1v60.lib  (slow corner)
```

Or use the open_pdks installation:
- https://github.com/RTimothyEdwards/open_pdks

### ASAP7 (7nm Predictive)

Academic 7nm FinFET PDK from Arizona State University:

```bash
git clone https://github.com/The-OpenROAD-Project/asap7

# Liberty files in:
# asap7/asap7sc7p5t_27/LIB/
```

### FreePDK45 (45nm)

Academic PDK from NCSU:

- Download: https://www.eda.ncsu.edu/wiki/FreePDK45
- Liberty files included in the download

### Generic (No Cell Library)

For RTL-level synthesis without a specific technology:

```bash
aly synth --module cpu --tool yosys --part generic
```

This produces a technology-independent netlist using Yosys's internal cell library.

## FPGA Synthesis

### Vivado (Xilinx)

```yaml
tools:
  vivado:
    bin: vivado
    threads: 8
    batch_opts:
      - "-mode"
      - "batch"

targets:
  arty_a7:
    tool: vivado
    part: xc7a100tcsg324-1
    top: fpga_top
    constraints:
      - constraints/arty_a7.xdc
    options:
      strategy: "Flow_PerfOptimized_high"
```

Run:
```bash
aly synth --module cpu --tool vivado --part xc7a100tcsg324-1
```

### Yosys + nextpnr (Lattice, Gowin)

For iCE40 FPGAs:
```bash
aly synth --module blinky --tool yosys --part ice40
```

For ECP5 FPGAs:
```bash
aly synth --module uart --tool yosys --part ecp5
```

For Gowin FPGAs:
```bash
aly synth --module spi --tool yosys --part gowin
```

## Parallel Jobs

Both Vivado and Yosys support parallel execution:

```bash
# Run synthesis with 8 threads
aly synth --module cpu --tool vivado -j 8

# Yosys ABC also supports threading
aly synth --module cpu --tool yosys -j 4
```

Configure default threads in synth.yaml:

```yaml
tools:
  vivado:
    threads: 8
  yosys:
    threads: 4
```

## Synthesis Reports

After synthesis, reports are generated in `build/synth/<tool>/<module>/reports/`:

### Vivado Reports
- `utilization.rpt` - Resource utilization
- `timing_summary.rpt` - Timing analysis
- `power.rpt` - Power estimation
- `drc.rpt` - Design rule checks

### Yosys Reports
- `stats.txt` - Cell and wire counts
- `check.txt` - Design checks
- `hierarchy.txt` - Module hierarchy

View reports with `--report` flag:
```bash
aly synth --module cpu --tool vivado --report
```

## Constraints

### Vivado (XDC)

```tcl
# constraints/arty_a7.xdc
create_clock -period 10.0 [get_ports clk]
set_property PACKAGE_PIN E3 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]
```

### Yosys/OpenROAD (SDC)

```tcl
# constraints/timing.sdc
create_clock -period 10.0 -name clk [get_ports clk]
set_input_delay -clock clk 2.0 [all_inputs]
set_output_delay -clock clk 2.0 [all_outputs]
```

Specify constraints in the target configuration:

```yaml
targets:
  arty_a7:
    tool: vivado
    part: xc7a100tcsg324-1
    constraints:
      - constraints/arty_a7.xdc
```

## Troubleshooting

### "Tool not found"

Ensure the tool is in your PATH or specify the full path:

```yaml
tools:
  yosys:
    bin: /opt/oss-cad-suite/bin/yosys
  vivado:
    bin: /tools/Xilinx/Vivado/2023.2/bin/vivado
```

### "Liberty file not found"

Check that the path is relative to project root or absolute:

```yaml
libraries:
  sky130_hd:
    liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib  # Relative to project root
```

### "Timing not met" (Vivado)

The timing report indicates setup/hold violations. Options:
1. Reduce clock frequency
2. Add timing constraints
3. Use a faster synthesis strategy:

```yaml
targets:
  fast:
    tool: vivado
    options:
      strategy: "Flow_PerfOptimized_high"
```

### Yosys VHDL Support

Yosys doesn't natively support VHDL. Options:
1. Use GHDL plugin: `yosys -m ghdl`
2. Convert VHDL to Verilog first
3. Use a different tool (Vivado, Genus)
