'''
Simple layered configuration

Blends together settings based on filter values.

One can define global settings without any filters. Then provide specialization for 
specific filters. A possible usage is to customize behaviour of a submodule based on
the banner it processes... 

Created on 2012.04.19.

@author: vhermecz
'''
import os
import glob
from django.dispatch.dispatcher import receiver
from onionconfig.signals import onion_config_updated
import logging
from onionconfig.utils import memoize
from types import DictType, ListType
from onionconfig.special_values import DynamicValue, ExplicitNone,\
    normalize
from copy import deepcopy
from django.conf import settings
import traceback
import json
import email
from datetime import datetime

logger = logging.getLogger("onionconfig")

class Config(object):
    """
    Reloadable main config
    """

    dimensions = {}
    context = {}
    expansions = []
    directory = None

    lazy_init_module = None

    def __init__(self, module_name=None):
        self.lazy_init_module = module_name

    def __getattribute__(self, attr):
        """
        Lame way of providing lazy init, should be enhanced
        """
        if attr not in ["lazy_init_module","update"] and self.lazy_init_module != None:
            self.update(self.lazy_init_module)
        return super(Config, self).__getattribute__(attr)

    def update(self, module_name):
        """
        Update config
        """
        self.lazy_init_module = None
        module = __import__(module_name, fromlist=[""])
        self.dimensions = dict((dim.name,dim) for dim in module.DIMENSIONS)
        self.context = getattr(module, "CONTEXT", {})
        self.expansions = getattr(module, "EXPANSIONS", [])
        dir_ = module.LAYER_CONFIG_DIR
        if os.path.isfile(dir_):
            dir_ = os.path.dirname(dir_)
        self.directory = dir_

class Layer(object):
    '''
    Stores a set of settings for a filtering
    '''
    def __init__(self, fname):
        data = eval(open(fname, "rb").read(), config.context)
        #data = simplejson.load(open(fname, "rb"))
        assert isinstance(data, dict)
        filters = Layer._normalize_filters(data.pop("__filter", None))
        self.priority = data.pop("__priority", None) or max(sum([config.dimensions[dim].priority_class for dim in filter_.keys()]) for filter_ in filters)
        self.filters = Layer._expand_filters(filters)
        self.name = data.pop("__name", None) or os.path.splitext(os.path.basename(fname))[0]
        self.data = data
        self.lmod = None
        self._dbg_fname = fname

    @staticmethod
    def _validate(data):
        if data.get("__priority", 1)<=0:
            raise ValueError, "Priority must be a positive integer"
        for dim in set([key for filter_ in Layer._preprocess_filter(data.get("__filter")) for key in filter_.keys()]):
            if not config.dimensions.has_key(dim):
                raise ValueError, "Unknown dimension used"

    @staticmethod
    def _normalize_filters(filters):
        if filters == None:
            filters = {}
        if type(filters) == DictType:
            filters = [filters]
        for filter_ in filters:
            for dim, value in filter_.iteritems():
                if type(value) != ListType:
                    value = [value]
                value = set(value)
                filter_[dim] = value
        return filters

    @staticmethod
    def _expand_filters(filters):
        # TODO(vhermecz): order expansions to the right order
        for expansion in config.expansions:
            new_filters = []
            for filter_ in filters:
                if filter_.has_key(expansion.source_dimension_name):
                    target_values = []
                    for value in filter_[expansion.source_dimension_name]:
                        target_values.extend([normalize(expansion.target_dimension_name, target_value) for target_value in expansion.expand(value)])
                    new_filter = deepcopy(filter_)
                    del new_filter[expansion.source_dimension_name]
                    new_filter[expansion.target_dimension_name] = set(target_values)
                    new_filters.append(new_filter)
#                    print "Expanded", filter_, "to", new_filter
            filters.extend(new_filters)
        return filters

    @staticmethod
    def _preprocess_filters(filters):
        filters = Layer._normalize_filters(filters)
        filters = Layer._expand_filters(filters)
        return filters

    def matches_filter(self, filter_):
        '''
        Detects if this layer matches the actual filter
        '''
        for layer_filter in self.filters:
            res = True
            for key, value in layer_filter.items():
                if filter_.get(key) not in value:
                    res = False
                    break
            if res == True:
                return True
        return False

    def get_priority(self):
        return self.priority

def _get_config_root():
    return config.directory

INVALID_CONFIG_FILES = []

@memoize
def get_layers(config_type=None):
    '''
    Load all the configuration files
    '''
    # can't yield, cause currently used memoize is not generator friendly
    res = []
    if config_type:
        path = os.path.join(_get_config_root(), config_type, "*.cfg")
    else:
        path = os.path.join(_get_config_root(), "*.cfg")

    for fname in glob.glob(path):
        try:
            res.append(Layer(fname))
        except Exception:
            global INVALID_CONFIG_FILES
            INVALID_CONFIG_FILES.append(fname)
            traceback.print_exc()
            logger.error("Invalid configuration layer")
    res = [item[1] for item in sorted((config.get_priority(), config) for config in res)]
    res = list(reversed(res))
    return res


def get_applicable_layers(config_type, filters):
    return [layer for layer in get_layers(config_type) if layer.matches_filter(filters)]

@memoize
def _get_full_config(config_type, filters):
    '''
    Get all applicable config layers for filter
    '''
    # print "get_full_config for ", filters
    def unify_config(high, low):
        '''
        Merge two layers of configuration.

        Dicts are blended together, for other constructs high is preferred
        '''
        assert high == None or isinstance(high, dict)
        assert low == None or isinstance(low, dict)
        res = dict()
        for key in set(high.keys()) | set(low.keys()):
            high_value = high.get(key)
            low_value = low.get(key)
            if type(high_value) == type(low_value) and type(high_value)==DictType:
                value = unify_config(high_value, low_value)
            else:
                value = high_value if high_value!=None else low_value
                value = deepcopy(value) # TODO(vhermecz) only needed if contains DynamicValue
                if isinstance(value, DynamicValue):
                    print "Dynvalue in unifyconfig"
                    value = value.evaluate(filters)
            res[key] = value
        return res

    def finalize_config(config):
        # TODO(vhermecz): skips postporcessing of lists
        for key, value in config.iteritems():
            if isinstance(value, ExplicitNone):
                value = None
                config[key] = value
            elif isinstance(value, DynamicValue):
                print "Dynvalue in finalize_config"
                value = value.evaluate(filters)
                config[key] = value
            elif type(value) == DictType:
                finalize_config(value)

    real_configs = get_applicable_layers(config_type, filters)
    real_configs = [item.data for item in real_configs]
    if len(real_configs)==0:
        return None
    real_config = reduce(unify_config, real_configs, {})
    finalize_config(real_config)
    return real_config


def _normalize_filter(filters):
    '''
    Remove unicode values, as only str should be used here
    Remove entries with None as value
    '''
    return dict((k, str(v)) for k,v in filters.items() if v!=None)


def get_config(path, config_type=None, **filters):
    '''
    Get a subhierarchy of configuration
    '''
    filters = _normalize_filter(filters)
    config = _get_full_config(config_type, filters)
    if isinstance(path, unicode):
        path = path.encode("UTF-8")
    if path in (None, ""):
        path = []
    elif isinstance(path, str):
        path = path.split(".")
    return reduce(lambda base, prop: base and base.get(prop), path, config)


@receiver(signal=onion_config_updated)
def config_update_receiver(sender, **kwargs):
    _get_full_config.clear()
    get_layers.clear()
    config.update(settings.ONION_CONFIG_SETTINGS)

config = Config(settings.ONION_CONFIG_SETTINGS)

