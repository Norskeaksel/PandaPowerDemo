from glob import glob
import warnings
import traceback
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandapower.plotting as plot
import pandapower.plotting.colormaps as cmaps
from pandapower.run import runpp
from pandapower.converter.cim import from_cim as cim2pp

warnings.simplefilter(action="ignore", category=FutureWarning)

try:
    net = cim2pp.from_cim(file_list=glob("CimFiles/*.xml"))
    plot.create_generic_coordinates(net, overwrite=True)
    runpp(net)
    print("PF_CONVERGED:", net.converged)
    cmap, norm = cmaps.cmap_continuous([(0.9, "blue"), (1.0, "green"), (1.1, "red")])
    sizes = plot.get_collection_sizes(net)
    cols = [
        plot.create_bus_collection(net, net.bus.index.values, cmap=cmap, norm=norm, size=sizes["bus"], zorder=2),
        plot.create_line_collection(net, net.line.index.values, use_bus_geodata=True, size=sizes["line"]),
    ]
    if len(net.trafo):
        cols.append(plot.create_trafo_collection(net, net.trafo.index.values, size=sizes["trafo"]))
    plot.draw_collections(cols)
    plt.savefig("cim_plot.png", dpi=120)
    print("SAVED cim_plot.png trafos", len(net.trafo))
except Exception:
    print("ERROR_TRACEBACK_START")
    traceback.print_exc()
    print("ERROR_TRACEBACK_END")
