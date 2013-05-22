'''
Created on 2012.05.23.

@author: vhermecz
'''
from django.db.models.base import Model
from django.db.models.fields import FieldDoesNotExist, Field
import re
from django.core.exceptions import ObjectDoesNotExist
import logging
from types import StringType

logger = logging.getLogger("onionconfig")


class BaseDimension(object):
    """
    Root class for onoinconfig dimensions
    
    A dimension defines a filtering for config retrieval.
    @ivar label: The label of dimension as represented on the UI
    @ivar name: The programmatic name as how the dimension is referred to in filters
    @ivar description: A longer definition of the dimension
    @ivar priority_class: The priority value assigned to this dimension
    @ivar valuset: The values the dimension holds
    
    Dimensions should be defined in the main onionconfig configuration file
    
    """
    label = None
    name = None
    description = None
    priority_class = 0
    valueset = []
    
    def __init__(self, name, label=name, description=None, priority_class=0, valueset = list()):
        self.name = name
        self.label = label
        self.description = description
        self.priority_class = priority_class
        self.valueset = valueset
        
    def normalize_value(self, value):
        if type(value) == StringType:
            return value
        else:
            raise NotImplementedError

    def is_valid_value(self, value):
        return value in self.get_valueset()
        
    def get_valueset(self):
        """
        The values supported by this dimension
        """
        return self.valueset

def case_camel_to_underscore(name):
    """
    Convert CamelCase identifiers to underscore_style_ones.
    @note: Could be moved to utils
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class DynamicValueset(object):
    """
    Dynamically evaluable valueset
    @note: Dynamic approach is not currently utilized
    """
    def __init__(self):
        pass
    def get_values(self):
        raise NotImplementedError
    @staticmethod
    def for_field(field):
        has_choices = len(field.flatchoices)
        if has_choices:
            return DBChoiceDynamicValueset(field)
        else:
            return DBValuesDynamicValueset(field)

class DBChoiceDynamicValueset(DynamicValueset):
    """
    Model field based Valuset for fields with choice constraint 
    """
    def __init__(self, field):
        super(DBChoiceDynamicValueset, self).__init__()
        assert isinstance(field, Field)
        self.field = field
    def get_values(self):
        return (k for k,v in self.field.flatchoices)

class DBValuesDynamicValueset(DynamicValueset):
    """
    Model field based Valueset based on field values in DB
    """
    def __init__(self, field):
        super(DBValuesDynamicValueset, self).__init__()
        assert isinstance(field, Field)
        self.field = field
    def get_values(self):
        # from http://stackoverflow.com/questions/2526445/django-query-to-get-a-unique-set-based-on-a-particular-columns-value
        return list(self.field.model.objects.values_list(self.field.name, flat=True).distinct())

class ModelFieldDimension(BaseDimension):
    """
    Model fields based dimension
    
    @ivar name: Default name is the lowercase table name for primary keys, otherwise extended with underscore_style field_name
    @ivar label: Default label is table/field verbose name depending on whether field is primary key
    @ivar description: Defaults to the label
  
    """
    def __init__(self, model, field_name, name=None, label=None, description=None, priority_class=0):
        if not issubclass(model, Model):
            raise ValueError, "model should be subclass of Django base model"
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            raise ValueError, "field does not exists in model"
        if not name:
            name = model._meta.module_name
            if not field.primary_key:
                name += "_" + case_camel_to_underscore(field.name)
        if not label:
            if not field.primary_key:
                label = field.verbose_name
            else:
                label = model._meta.verbose_name
        if not description:
            description = label
        valueset = DynamicValueset.for_field(field).get_values()
        super(ModelFieldDimension, self).__init__(name, label, description, priority_class, valueset)
        self.model = model
        self.field_name = field_name

    def normalize_value(self, value):
        """
        Object dimension value converted to string repr
        """
        if isinstance(value, self.model):
            return getattr(value, self.field_name)
        return value
    
    def denormalize_value(self, value):
        """
        String repr of dimension value converted to object
        """
        try:
            return self.model.objects.get(**{self.field_name:value})
        except ObjectDoesNotExist:
            logger.error("denormalize called on invalid value. Probably due to missing validation")

class Expansion(object):
    """
    Expand a dimension filter value into another dimension
    @ivar source_dimension_name: Name of the source dimension
    @ivar target_dimension_name: Name of the target dimension
    @ivar expansion_function: The expansion operation
    
    Expansion function should return a list of values in the target dimension either in normalized or denormalized format 
    """
    def __init__(self, source_dimension_name, target_dimension_name, expansion_function):
        self.source_dimension_name = source_dimension_name
        self.target_dimension_name = target_dimension_name
        self.expansion_function = expansion_function
    def expand(self, source_value):
        try:
            return self.expansion_function(source_value)
        except Exception:
            pass
