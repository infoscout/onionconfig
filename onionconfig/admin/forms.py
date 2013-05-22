'''
Created on 2012.05.03.

@author: vhermecz
'''
from django.forms import widgets
from django import forms
from django.forms.fields import Field, ChoiceField
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
#from onionconfig.config import config
import onionconfig.config


class FilterForm(forms.Form):
    path = forms.CharField(max_length=128, label="Path", required=False)
    def __init__(self, *largs, **kwargs):
        super(FilterForm, self).__init__(*largs, **kwargs)
        
        config = onionconfig.config.config
        
        for dim in config.dimensions.values():
            choices = (("", "**nothing**"),) +  tuple((value, value) for value in dim.get_valueset())
            self.fields[dim.name] = ChoiceField(label=dim.label, help_text=dim.description, choices=choices, required=False)
