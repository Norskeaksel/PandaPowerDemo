"""Load a CGMES 2.4.15 model (EQ + SSH + TP + SV) into pandapower."""

import logging
from pathlib import Path

import pandapower as pp
from pandapower.converter.cim import from_cim as cim2pp
logging.basicConfig(level=logging.INFO)

CIM_DIR = Path(__file__).parent / "_ignore_situation_files"

# The converter detects each profile from the md:Model.profile header,
# so the order of the files does not matter.
file_list = [
    str(CIM_DIR / "EC-2.4.xml"),  # EQ  - EquipmentCore
    str(CIM_DIR / "SSH.xml"),     # SSH - SteadyStateHypothesis
    str(CIM_DIR / "TP.xml"),      # TP  - Topology
    str(CIM_DIR / "SV.xml"),      # SV  - StateVariables
]

net = cim2pp.from_cim(
    file_list=file_list,
    cgmes_version="2.4.15",
    use_sv_data_for_assets=True,   # take operating points from the SV profile
    create_measurements="SV",      # build measurements from SV power flows
    run_powerflow=False,
    ignore_errors=True,
)

print(net)

# Solve the imported network
pp.runpp(net)
print(net.res_bus.describe())
