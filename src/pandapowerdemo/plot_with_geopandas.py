import webbrowser
from pathlib import Path

import folium
import pandapower as pp
import geopandas as gpd
import shapely
import xyzservices.providers as xyz

def plot_with_geopandas(net):
    lines = gpd.GeoDataFrame(
        net.line.copy(),
        geometry=shapely.from_geojson(net.line["geo"]),
        crs=4326, # GPS
        )
    buses = gpd.GeoDataFrame(
        net.bus.copy(),
        geometry=shapely.from_geojson(net.bus["geo"]),
        crs=4326,
    )
    buses["pu"] = net.res_bus["vm_pu"]
    lines["loading_percent"] = net.res_line["loading_percent"]
    m = lines.explore(
        tiles= xyz.Esri.WorldGrayCanvas, # "CartoDB positron" shows API-KEY required on the map
        column="loading_percent", # The column to color by!
        cmap="coolwarm",
        vmax=100,
        name="lines",
        )
    m = buses.explore(
        m=m,  # buses need to go in the same map --> m=m
        column="pu",
        cmap="coolwarm",
        marker_kwds={"radius": 6},
        name="buses",
        )
    ext_grid_buses = buses.loc[net.ext_grid["bus"]]
    m = ext_grid_buses.explore(
        m=m,
        color="yellow",
        marker_kwds={"radius": 8},
        name="external grids",
        )
    if not net.gen.empty:
        gen_buses = buses.loc[net.gen["bus"]].copy()
        gen_buses["generation_mw"] = net.res_gen["p_mw"].values
        m = gen_buses.explore(
            m=m,
            color="purple",
            marker_kwds={"radius": 8},
            name="generators",
            )
    folium.LayerControl().add_to(m)
    nr_of_generators = len(net.gen)
    output_path = Path("plots") / f"mv_net_{nr_of_generators}.html"
    output_path.parent.mkdir(exist_ok=True)
    m.save(str(output_path))
    webbrowser.open(output_path.resolve().as_uri())
    print(f"interactive map generated and saved as '{output_path}'")
