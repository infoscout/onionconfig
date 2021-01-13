'''
Created on 2012.05.03.

@author: vhermecz
'''
#from onionconfig.config import config
import onionconfig.config
from django import forms
from django.forms.fields import ChoiceField


class FilterForm(forms.Form):
    path = forms.CharField(max_length=128, label="Path", required=False)

    def __init__(self, *largs, **kwargs):
        super(FilterForm, self).__init__(*largs, **kwargs)

        config = onionconfig.config.config

        for dim in list(config.dimensions.values()):
            choices = (("", "**nothing**"),) + tuple((value, value) for value in dim.get_valueset())
            self.fields[dim.name] = ChoiceField(
                label=dim.label, help_text=dim.description, choices=choices, required=False)
