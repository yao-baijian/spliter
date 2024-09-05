# RTL -> DAG splitter v0.1

## Note:
RTL Synthesizer YOSYS taken from [yosys] (https://github.com/YosysHQ/yosys)

RTL parser taken from [pyverilog] (https://github.com/PyHDI/Pyverilog) 

DAG generator taken from [MasterRTL] (https://github.com/hkust-zhiyao/MasterRTL)

## Working principle:

spliter read in synthesized RTL code, and generate 2 output RTL, first one contain all register critical path, second one exclude the critical path
