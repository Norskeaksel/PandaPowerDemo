import pandapower as pp

net = pp.networks.mv_oberrhein()
pp.runpp(net)
pp.plotting.plotly.pf_res_plotly(net)
