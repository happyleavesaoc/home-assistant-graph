"""Console app.

Usage:

    python3 -m hagraph -i <path/to/configuration.yaml> -o <path/to/output.[dot/png/jpg/etc]>

"""

import argparse
import os.path
from homeassistant.config import load_yaml_config_file
from networkx.drawing.nx_agraph import to_agraph
from hagraph import make_graph

DEFAULT_PROG = 'neato'


def main():
    """Generate graph of Home Assistant config."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', help='path to configuration.yaml', required=True)
    parser.add_argument('-o', '--output-file', help='graphviz file to write', required=True)
    parser.add_argument('-p', '--prog', default=DEFAULT_PROG, help='graphviz program')
    args = vars(parser.parse_args())
    conf = load_yaml_config_file(os.path.abspath(args.get('input_file')))
    graph = make_graph(conf)
    to_agraph(graph).draw(args.get('output_file'), prog=args.get('prog'))


if __name__ == '__main__':
    main()
