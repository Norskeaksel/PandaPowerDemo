import pandapower as pp
import pandapower.topology as top
from pathlib import Path

from lxml import etree
from pandapower.converter.cim import cim_classes
from pandapower.converter.cim import from_cim as cim2pp

CGMES_VERSION = '2.4.15'
RDF_RESOURCE = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'
PP_ELEMENTS = ['bus', 'dcline', 'ext_grid', 'gen', 'impedance', 'line', 'load', 'motor', 'sgen', 'shunt',
               'storage', 'switch', 'trafo', 'trafo3w', 'ward', 'xward']
# CGMES leaves these optional; pandapower needs plain numpy bools for the numba power flow kernels.
BOOL_DEFAULTS = {'in_service': True, 'closed': True}


def normalize_bool_columns(net) -> dict[str, int]:
    """Replace pd.NA in boolean columns with CGMES defaults and return how many were filled per column."""
    filled = {}
    for element in PP_ELEMENTS:
        if element not in net:
            continue
        df = net[element]
        for column, default in BOOL_DEFAULTS.items():
            if column not in df.columns:
                continue
            missing = int(df[column].isna().sum())
            if missing:
                filled[f'{element}.{column}'] = missing
            df[column] = df[column].fillna(default).astype(bool)
    return filled


class ResourceProfileCimParser(cim_classes.CimParser):
    """Accepts FullModel headers that state Model.profile as an rdf:resource attribute instead of element text."""

    def _get_cgmes_profile_from_xml(self, root: etree._Element, default_profile: str = 'unknown') -> str:
        for header in root:
            if not isinstance(header.tag, str) or 'FullModel' not in header.tag:
                continue
            for child in header:
                if not isinstance(child.tag, str) or not child.tag.endswith('Model.profile'):
                    continue
                if not (child.text and child.text.strip()) and RDF_RESOURCE in child.attrib:
                    child.text = child.attrib.pop(RDF_RESOURCE)
        return super()._get_cgmes_profile_from_xml(root, default_profile)


def reduce_slack_to_one_per_island(net) -> dict[str, int]:
    """Keep one voltage reference per galvanically connected island; demote the rest to PV generators."""
    if 'slack' not in net.gen.columns:
        return {}

    islands = list(top.connected_components(top.create_nxgraph(net, respect_switches=True)))
    bus_island = {bus: i for i, island in enumerate(islands) for bus in island}

    grid_islands = {bus_island.get(b) for b in net.ext_grid.loc[net.ext_grid.in_service, 'bus']}
    is_slack = net.gen.slack.fillna(False).astype(bool) & net.gen.in_service

    slack_by_island: dict[int, list[int]] = {}
    for idx in net.gen.index[is_slack]:
        slack_by_island.setdefault(bus_island.get(net.gen.at[idx, 'bus']), []).append(idx)

    demoted = 0
    for island, gens in slack_by_island.items():
        if island in grid_islands:
            keep = None
        elif 'sn_mva' in net.gen.columns and not net.gen.loc[gens, 'sn_mva'].isna().all():
            keep = net.gen.loc[gens, 'sn_mva'].idxmax()
        else:
            keep = gens[0]
        net.gen.loc[[g for g in gens if g != keep], 'slack'] = False
        demoted += len(gens) - (keep is not None)

    referenced = grid_islands | set(slack_by_island)
    stranded = [i for i in range(len(islands)) if i not in referenced]
    return {'islands': len(islands), 'demoted_slack_gens': demoted,
            'islands_without_reference': len(stranded),
            'buses_without_reference': sum(len(islands[i]) for i in stranded)}


def describe_fragmentation(net) -> None:
    """Aggregate-only breakdown of why the network splits into islands."""
    from collections import Counter

    for label, respect in (("respecting switch states", True), ("all switches fused closed", False)):
        islands = list(top.connected_components(top.create_nxgraph(net, respect_switches=respect)))
        sizes = sorted((len(i) for i in islands), reverse=True)
        buckets = Counter('1 bus' if s == 1 else '2-5' if s <= 5 else '6-50' if s <= 50 else '>50' for s in sizes)
        print(f"  {label}: {len(islands)} islands, largest {sizes[0]}, buckets {dict(buckets)}")

    energised = set()
    for element in ('load', 'sgen', 'gen', 'ext_grid'):
        df = net[element]
        energised |= set(df.loc[df.in_service, 'bus'])
    islands = list(top.connected_components(top.create_nxgraph(net, respect_switches=True)))
    dead = [i for i in islands if not (i & energised)]
    print(f"  islands with no load/gen at all: {len(dead)} covering {sum(len(i) for i in dead)} buses")

    sw = net.switch
    print("  switches:", len(sw), "open:", int((~sw.closed.astype(bool)).sum()),
          "by type:", sw.et.value_counts().to_dict())
    print("  buses:", len(net.bus), "in service:", int(net.bus.in_service.sum()),
          "| trafo:", len(net.trafo), "trafo3w:", len(net.trafo3w), "line:", len(net.line))


situation_dir = Path(__file__).resolve().parents[1] / "_ignore_situation_files"
cgmes_files = sorted(str(p) for p in situation_dir.glob("*.xml"))
print(cgmes_files)

cim_parser = ResourceProfileCimParser(cgmes_version=CGMES_VERSION)
cim_parser.parse_files(file_list=cgmes_files, prepare_cim_net=True, set_data_types=True)

# TapChanger.discrete is absent from this export, so the tap controllers cannot be typed
# zero-reactance ACLineSegments (jumpers) become switches; r_limit is negative so only the x arm can match
net = cim2pp.from_cim_dict(cim_parser, cim_version=CGMES_VERSION, create_tap_controller=False,
                           convert_line_to_switch=True, line_r_limit=-1.0, line_x_limit=0.0)
print("NET LOADED! Running power flow!")
print("filled boolean gaps:", normalize_bool_columns(net))
print("fragmentation:")
describe_fragmentation(net)
print("slack reduction:", reduce_slack_to_one_per_island(net))

pp.rundcpp(net, check_connectivity=True)
print("DC power flow solved. buses with results:", len(net.res_bus), "lines:", len(net.res_line))
print("max |line loading| %:", round(float(net.res_line.loading_percent.abs().max()), 1))
print("line loading %% quantiles:", {q: round(float(net.res_line.loading_percent.abs().quantile(q)), 2)
                                     for q in (0.5, 0.9, 0.99, 1.0)})
print("trafo loading %% max:", round(float(net.res_trafo.loading_percent.abs().max()), 1),
      "median:", round(float(net.res_trafo.loading_percent.abs().median()), 2))
print("max |line p_mw|:", round(float(net.res_line.p_from_mw.abs().max()), 2),
      "max |trafo p_mw|:", round(float(net.res_trafo.p_hv_mw.abs().max()), 2))
print("slack absorbed MW:", round(float(net.res_gen.p_mw.sum() - net.gen.p_mw.sum()), 1))
print("in-service totals MW - load:", round(float(net.load.loc[net.load.in_service, 'p_mw'].sum()), 1),
      "sgen:", round(float(net.sgen.loc[net.sgen.in_service, 'p_mw'].sum()), 1),
      "gen:", round(float(net.gen.loc[net.gen.in_service, 'p_mw'].sum()), 1))
print("energised buses in results:", int(net.res_bus.p_mw.notna().sum()),
      "line rating median kA:", round(float(net.line.max_i_ka.median()), 3))