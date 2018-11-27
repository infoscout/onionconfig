'''
Created on 2012.05.23.

@author: vhermecz
'''
import logging

from onionconfig.metaconfig import ModelFieldDimension


logger = logging.getLogger("onionconfig")


class ExplicitNone(object):
    """
    Explicit marker for None
    
    While None values are overridden by layers with lower priority,
    the explicit None is accepted as the real value, rendered as
    None in the result
    """
    def __init__(self):
        pass


class DynamicValue(object):
    """
    Baseclass for dynamic config value
    
    Evaluated in the context of the filter applied for setting retrieval
    """
    def __init__(self):
        pass

    def evaluate(self, filters):
        """
        Return actual value of the setting
        
        @note Default behavoiur is to be transparent
        @note Return ExplicitNone if None is intended to be the actual value
        """
        return None


class ModelDimensionValue(DynamicValue):
    """
    Retrieve model property as part of settings
    """
    def __init__(self, dimension_name, field_name):
        super(ModelDimensionValue, self).__init__()
        self.dimension_name = dimension_name
        self.field_name = field_name
    
    def evaluate(self, filters):
        if filters.has_key(self.dimension_name):
            obj = denormalize(self.dimension_name, filters[self.dimension_name])
            if obj is None:
                return None
            try:
                return getattr(obj, self.field_name)
            except AttributeError:
                return None


def denormalize(dimension_name, value):
    """
    Retrieve object representation of a dimension value
    
    TODO(vhermecz): ducktyping should be used instead of inheritence 
    """
    from onionconfig.config import config
    dimension = config.dimensions.get(dimension_name)
    if not isinstance(dimension, ModelFieldDimension):
        logger.error("denormalize called on dimension not supporting it")
        return None
    object_ = dimension.denormalize_value(value)
    return object_


def normalize(dimension_name, value):
    """
    Convert object representation of a dimension value into string
    
    TODO(vhermecz): ducktyping should be used instead of inheritence 
    """
    if isinstance(type(value), str):
        return value
    from onionconfig.config import config
    dimension = config.dimensions.get(dimension_name)
    if not isinstance(dimension, ModelFieldDimension):
        logger.error("normalize called on dimension not supporting it")
        return None
    return dimension.normalize_value(value)
