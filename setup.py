from setuptools import find_packages, setup


with open('VERSION', 'r') as f:
    version = f.read().strip()


setup(
    name='onionconfig',
    packages=find_packages(),
    include_package_data=True,
    description='Inheritable configuration',
    url='http://github.com/infoscout/onionconfig',
    version=version,
    install_requires=[
        'Django>=1.8',
    ]
)
