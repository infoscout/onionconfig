'''
Created on 2012.05.24.

@author: vhermecz
'''
from collections import namedtuple

ResultSetItem = namedtuple("ResultSetItem", "name priority filename is_active")


def create_layer_list(filters):
    from onionconfig.config import get_layers, get_applicable_layers

    data = []
    all_layers = get_layers()
    active_layers = get_applicable_layers(filters)
    active_layers_set = set(active_layers)
    for layer in all_layers:
        item = ResultSetItem(layer.name, layer.priority, layer._dbg_fname, layer in active_layers_set)
        data.append(item)
    return data
