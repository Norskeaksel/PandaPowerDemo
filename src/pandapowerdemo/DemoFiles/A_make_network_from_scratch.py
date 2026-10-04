import pandapower as pp
from pandapower.plotting.plotly import pf_res_plotly
from math import sqrt

net = pp.create_empty_network()
slack_bus = pp.create_bus(net, vn_kv=300, geodata=(1, 2))
load_bus1 = pp.create_bus(net, vn_kv=300, geodata=(2, 2))
load_bus2 = pp.create_bus(net, vn_kv=300, geodata=(1, 1))
load_bus3 = pp.create_bus(net, vn_kv=300, geodata=(2, 1))

pp.create_ext_grid(net, bus=slack_bus)

pp.create_load(net, bus=load_bus1, p_mw=5)
pp.create_load(net, bus=load_bus2, p_mw=15)
pp.create_load(net, bus=load_bus3, p_mw=25)

line_params = {"r_ohm_per_km": 0.01, "x_ohm_per_km": 0.4, "c_nf_per_km": 0.0, "max_i_ka": 20 / (300 * sqrt(3))}
pp.create_line_from_parameters(net, from_bus=slack_bus, to_bus=load_bus1, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=slack_bus, to_bus=load_bus2, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=slack_bus, to_bus=load_bus3, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=load_bus1, to_bus=load_bus3, length_km=1, **line_params)
pp.create_line_from_parameters(net, from_bus=load_bus2, to_bus=load_bus3, length_km=1, **line_params)

pp.runpp(net)
pf_res_plotly(net, auto_open=False)
