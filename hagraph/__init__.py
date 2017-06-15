"""Generate a Graphviz file based on a Home Assistant configuration file.

Usage:

    hagraph -i <path/to/configuration.yaml> -o <path/to/output.[dot/png/jpeg/etc]>

"""

import homeassistant.const as const
from homeassistant.util import slugify
import networkx


LABEL_CONTAINS = 'contains'
ATTR_COLOR = 'color'
ALL_DOMAINS = {
    'light': 'lights',
    'switch': 'switches',
    'device_tracker': 'devices',
    'lock': 'locks'
}
DOMAIN_COLORS = {
    'light': 'yellow',
    'switch': 'blue',
    'device_tracker': 'purple',
    'lock': 'red',
    'script': 'brown',
    'scene': 'turquoise',
    'media_player': 'orange',
    'sensor': 'green',
    'binary_sensor': 'green',
    'group': 'cyan'
}
ATTR_GRAPH = {
    'graph': {
        'bgcolor': '#E5E5E5',
        'splines': 'curved',
        'overlap': 'false'
    },
    'node': {
        'fillcolor': 'white',
        'fontcolor': '#212121',
        'fontname': 'arial',
        'fontsize': 10.5,
        'margin': '0.15,0.05',
        'shape': 'rectangle',
        'style': 'filled'
    },
    'edge': {
        'arrowhead': 'open',
        'arrowsize': 0.75,
        'fontcolor': '#212121',
        'fontname': 'arial',
        'fontsize': 10.5
    }
}


def new_graph():
    """Get a clean graph."""
    graph = networkx.MultiDiGraph()
    graph.graph = ATTR_GRAPH
    return graph


def get_entity_id(domain, name):
    """Format domain and name into entity id."""
    return const.PLATFORM_FORMAT.format(domain, slugify(name))


def get_domain(entity_id):
    """Get domain portion of entity id."""
    return entity_id.split('.')[0]


def bool_string(state):
    """Get string equivalent of boolean state."""
    if isinstance(state, dict) and const.CONF_STATE in state:
        state = state[const.CONF_STATE]
    return const.STATE_ON if state else const.STATE_OFF


def get_all_group(name):
    """Get `all` group entity id based on domain."""
    return 'group.all_{}'.format(ALL_DOMAINS.get(name, name))


def get_entity_ids(obj):
    """Extract entity id(s) from HASS-like structures."""
    if 'data' in obj:
        return get_entity_ids(obj['data'])
    if 'data_template' in obj:
        return get_entity_ids(obj['data_template'])
    if 'event_data' in obj:
        return get_entity_ids(obj['event_data'])
    if const.ATTR_ENTITY_ID not in obj:
        return []
    if isinstance(obj[const.ATTR_ENTITY_ID], list):
        return obj[const.ATTR_ENTITY_ID]
    elif isinstance(obj[const.ATTR_ENTITY_ID], str):
        return [obj[const.ATTR_ENTITY_ID]]
    elif obj[const.ATTR_ENTITY_ID] is None:
        raise ValueError('missing entities')


def entities_or_service(obj):
    """Get entities, or service if no entities."""
    try:
        entity_ids = get_entity_ids(obj)
    except ValueError:
        return []
    if entity_ids:
        return entity_ids
    if const.ATTR_SERVICE in obj:
        return [get_domain(get_service(obj))]
    else:
        return []


def get_service(data):
    """Get service name."""
    if const.ATTR_SERVICE in data:
        return data[const.ATTR_SERVICE]
    elif 'service_template' in data:
        return data['service_template']
    else:
        raise ValueError('no service')


def entities_or_platform(obj):
    """Get entities, or platform if no entities."""
    entity_ids = get_entity_ids(obj)
    if entity_ids:
        return entity_ids
    return [obj[const.CONF_PLATFORM]]


def add_packages(data, graph):
    """Add packages to graph."""
    for data in data.values():
        add_core_edges(data, graph)


def add_scene(data, graph):
    """Add scene to graph."""
    scene_entity = get_entity_id('scene', data[const.CONF_NAME])
    for entity, data in data[const.CONF_ENTITIES].items():
        graph.add_edge(scene_entity, entity, label=bool_string(data))


def add_group(name, data, graph):
    """Add group to graph."""
    group_entity = get_entity_id('group', name)
    if group_entity not in graph.node:
        return
    for entity in data:
        graph.add_edge(group_entity, entity, label=LABEL_CONTAINS)


def add_alexa(name, data, graph):
    """Add Alexa intent to graph."""
    intent_entity = get_entity_id('alexa', name)
    if 'action' not in data:
        return
    check = entities_or_service(data['action'])
    if len(check) > 0:
        target = check[0]
        graph.add_edge(intent_entity, target, label=get_service(data['action']))


def add_script(name, data, graph):
    """Add script to graph."""
    script_entity = get_entity_id('script', name)
    if isinstance(data['sequence'], list):
        for step in data['sequence']:
            add_script_step(step, graph, script_entity)
    else:
       add_script_step(data['sequence'], graph, script_entity)


def add_script_step(step, graph, script_entity):
    """Add script step."""
    if const.ATTR_SERVICE not in step and 'service_template' not in step:
        return
    for target in entities_or_service(step):
        graph.add_edge(script_entity, target, label=get_service(step))


def add_automation(data, graph):
    """Add automation to graph."""
    sources = []
    if isinstance(data['trigger'], list):
        for trigger in data['trigger']:
            sources += entities_or_platform(trigger)
    else:
        sources = entities_or_platform(data['trigger'])
    if 'action' in data and isinstance(data['action'], list):
        for action in data['action']:
            if 'service' not in action:
                continue
            for target in entities_or_service(action):
                for source in sources:
                    graph.add_edge(source, target, label=get_service(action))
    else:
        for target in entities_or_service(data['action']):
            for source in sources:
                graph.add_edge(source, target, label=get_service(data['action']))


def add_core_edges(conf, graph):
    """Add core edges to the graph."""
    for key in conf:
        if key.startswith('automation'):
            for data in conf[key]:
                add_automation(data, graph)
        elif key.startswith('script'):
            for name, data in conf[key].items():
                add_script(name, data, graph)
        elif key.startswith('scene'):
            for data in conf[key]:
                add_scene(data, graph)
        elif key.startswith('alexa'):
            for intent, data in conf[key]['intents'].items():
                add_alexa(intent, data, graph)
        elif key.startswith('homeassistant'):
            if 'packages' in conf[key]:
                add_packages(conf[key]['packages'], graph)


def add_group_edges(conf, graph):
    """Add group edges to the graph."""
    for key in conf:
        if key.startswith('group'):
            for name, data in conf[key].items():
                add_group(name, data, graph)
    for entity in graph.node:
        domain = get_domain(entity)
        group_name = get_all_group(domain)
        if domain in ALL_DOMAINS.keys() and group_name in graph.node:
            graph.add_edge(group_name, entity, label=LABEL_CONTAINS)


def color_graph(graph):
    """Color the graph."""
    for entity, data in graph.nodes(data=True):
        domain = get_domain(entity)
        if domain in DOMAIN_COLORS.keys():
            data[ATTR_COLOR] = DOMAIN_COLORS[domain]


def make_graph(conf):
    """Make the graph object."""
    graph = new_graph()
    add_core_edges(conf, graph)
    add_group_edges(conf, graph)
    color_graph(graph)
    return graph
