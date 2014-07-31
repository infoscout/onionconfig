from setuptools import find_packages
from isc_ops.setup_tools import setup, current_version

setup(name='onionconfig',
    packages=find_packages(), 
    include_package_data=True, 
    description = 'Inheritable configuration',
    url = 'http://github.com/infoscout/onionconfig',
    version = current_version(),    
    install_requires=[
        'django==1.4',
    ]
)

