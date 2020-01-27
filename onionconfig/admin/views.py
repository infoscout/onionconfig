from django.contrib import messages
from django.shortcuts import render

from onionconfig.admin.forms import FilterForm
from onionconfig.admin.helpers import create_layer_list
from onionconfig.config import get_config, INVALID_CONFIG_FILES
from onionconfig.signals import onion_config_updated


def view_status(request):
    
    if request.GET.get('reload', None) is not None:
        onion_config_updated.send(None)
    
    filter_form = FilterForm(request.GET)
    
    if filter_form.is_valid():
        cleaned_data = dict(filter_form.cleaned_data)
        path = cleaned_data.pop("path")
        filters = cleaned_data
    else:
        path = ""
        filters = {}

    filters = {k: v for k, v in filters.items() if len(v)}

    context = {
        'filter_form': filter_form,
        'view': get_config(path, **filters),
        'layers': create_layer_list(filters)
    }
    
    for fname in INVALID_CONFIG_FILES:
        messages.add_message(request, messages.ERROR, 'Invalid config file:' + fname)
    
    return render(request, 'admin/onionconfig/status.html', context)
