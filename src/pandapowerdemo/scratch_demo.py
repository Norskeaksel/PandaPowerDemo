import pandapower as pp
from pandapower.plotting.plotly import pf_res_plotly
from math import sqrt


net = pp.create_empty_network()

v = 300
slack_bus = pp.create_bus(net, vn_kv=v, geodata=(0, 1))
load_bus1 = pp.create_bus(net, vn_kv=v, geodata=(1, 1))
bus_load2 = pp.create_bus(net, vn_kv=v, geodata=(0, 0))
bus_load3 = pp.create_bus(net, vn_kv=v, geodata=(1, 0))

pp.create_ext_grid(net, bus=slack_bus)

pp.create_load(net, bus=load_bus1, p_mw=5)
pp.create_load(net, bus=bus_load2, p_mw=15)
pp.create_load(net, bus=bus_load3, p_mw=25)

line_params = {"r_ohm_per_km": 0.01, "x_ohm_per_km": 0.4, "c_nf_per_km": 0.0, "max_i_ka": 20/(v * sqrt(3))}
pp.create_line_from_parameters(net, from_bus=slack_bus, to_bus=load_bus1, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=slack_bus, to_bus=bus_load2, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=slack_bus, to_bus=bus_load3, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=load_bus1, to_bus=bus_load3, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=bus_load2, to_bus=bus_load3, length_km=1, **line_params)

pp.runpp(net)
pf_res_plotly(net)