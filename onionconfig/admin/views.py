from django.shortcuts import render
from onionconfig.config import get_config
from onionconfig.signals import onion_config_updated
from onionconfig.admin.forms import FilterForm
from onionconfig.admin.helpers import create_layer_list

def view_status(request):
    
    if request.GET.get('reload', None)!=None:
        onion_config_updated.send(None)
    
    filter_form = FilterForm(request.GET)
    
    if filter_form.is_valid():
        cleaned_data = dict(filter_form.cleaned_data)
        path = cleaned_data.pop("path")
        filters = cleaned_data
    else:
        path = ""
        filters = {}
    
    print repr(filters)
    filters = dict((k, v) for k,v in filters.items() if len(v))
    print repr(filters)

    context = {'filter_form': filter_form,
               'view': get_config(path, **filters),
               'layers': create_layer_list(filters)
               }
    
    return render(request, 'admin/onionconfig/status.html', context)
    
