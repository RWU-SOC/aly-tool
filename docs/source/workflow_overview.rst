Workflow Overview
=================

This page summarizes the recommended RTL/SoC/FPGA/ASIC development flow supported by ALY, inspired by industry best practices.

Parallel Tracks: RTL & Verification
-----------------------------------

The flow is organized as two parallel tracks that meet in simulation:

- **RTL track:** Hardware design (modules, interfaces, datapaths, FSMs)
- **Verification track:** UVM or non-UVM testbench, reference models, coverage

Spec & Planning
---------------
- Capture requirements: features, interfaces, corner cases, resets, timing
- Define verification plan: features to verify, scenarios, coverage goals

RTL Design Flow
---------------
- Interface definition: SystemVerilog modules, interfaces
- Internal architecture: block diagrams, pipelines, FIFOs, FSMs
- RTL coding: always_ff, always_comb, logic, enums, etc.
- Lint/basic checks: run lint tools, simple sims
- Sanity testbench: non-UVM, directed tests

Verification (UVM) Flow
-----------------------
- Define DUT interfaces (SystemVerilog interface)
- Build UVM components: sequence_item, sequence, sequencer, driver, monitor, agent, scoreboard, env, test
- Reference model & checkers: golden model, scoreboard, assertions
- Coverage: functional covergroups, coverage closure

Integrating RTL + Verification
- Run UVM tests: compile all RTL + UVM, run with simulator (Questa, VCS, Xcelium, etc.)
- Debug & iterate: fix bugs, refine tests, close coverage

Synthesis & Implementation
--------------------------
- Synthesis: run on clean RTL, check timing/area
- Gate-level simulation (optional): run UVM TB against netlist
- Implementation (P&R): place & route for FPGA/ASIC
- Signoff: STA, DRC, timing reports

Workflow Summary
----------------
- Spec → verification plan
- Write RTL (modules, interfaces, FSMs, datapaths)
- Build UVM environment (env, agents, sequences, scoreboard, coverage)
- Hook DUT + UVM together in a top testbench
- Run regressions, debug, close coverage
- Synthesize/implement RTL for target FPGA/ASIC

See :doc:`getting-started` for project structure and :doc:`commands` for available ALY commands.
