from setuptools import setup, find_packages

setup(name='onionconfig',
    packages=find_packages(),  
    description = 'Inheritable configuration',
    url = 'http://github.com/infoscout/onionconfig',
    version = '0.1dev',    
    install_requires=[
        'django>=1.4',
    ]
)

