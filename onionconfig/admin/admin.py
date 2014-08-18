from django.conf.urls.defaults import patterns, url
from isc_admin.admin_site import AdminApp
from onionconfig.admin.views import view_status


class OnionConfigAdminApp(AdminApp):
    def get_urls(self):
        urls = patterns('',
             url(r'^onionconfig/?$', self.admin_view(view_status), name='onionconfig_index'),
        )
        return urls

