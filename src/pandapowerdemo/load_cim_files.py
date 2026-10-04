import os
import warnings

import pandapower.plotting as plt
import pandapower.plotting.colormaps as cmaps
from pandapower.converter.cim import from_cim as cim2pp
from pandapower.run import runpp

warnings.simplefilter(action='ignore', category=FutureWarning)

# folder_path points to the directory where the CIM .zip-Files are stored:
folder_path = os.path.join(os.getcwd(), 'example_cim')

# cgmes_files is a list containing paths to both files needed for the CIM converter:
cgmes_files = [os.path.join(folder_path, 'CGMES_v2.4.15_SmallGridTestConfiguration_Boundary_v3.0.0.zip'),
               os.path.join(folder_path, 'CGMES_v2.4.15_SmallGridTestConfiguration_BaseCase_Complete_v3.0.0.zip')]

for f in cgmes_files:
    if not os.path.exists(f):
        raise UserWarning(f"Wrong path specified for the CGMES file {f}")

net = cim2pp.from_cim(file_list=cgmes_files, use_GL_or_DL_profile='DL')

print('Conversion successful')

runpp(net)
print(net.res_bus.iloc[0:5]) # print first few bus results

bus_geo = net.bus.geo.iloc[0]
net.bus.geo.fillna(bus_geo, inplace=True)

cmap_list = [(0.9, "blue"), (1.0, "green"), (1.1, "red")]
cmap, norm = cmaps.cmap_continuous(cmap_list)

sizes = plt.get_collection_sizes(net)

bc = plt.create_bus_collection(net,net.bus.index.values,cmap=cmap, size=sizes['bus'])
lc = plt.create_line_collection(net,net.line.index.values, use_bus_geodata=True)
tc = plt.create_trafo_collection(net,net.trafo.index.values, size=sizes["trafo"])
plt.draw_collections([bc,lc,tc])
plt.show()