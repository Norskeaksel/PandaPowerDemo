from glob import glob
from pandapower.converter.cim import from_cim as cim2pp

files = glob("**/_ignore_situation_files/*.xml", recursive=True)
print(files)
net = cim2pp.from_cim(
    file_list=files,
    cgmes_version="2.4.15",
)

print(net)
