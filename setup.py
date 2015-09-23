#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages()
desc = open("README.md").read(),

setup(
    name='mapzen.whosonfirst.export',
    namespace_packages=['mapzen', 'mapzen.whosonfirst', 'mapzen.whosonfirst.export'],
    version='0.55',
    description='Simple Python wrapper for managing Who\'s On First export-related functions',
    author='Mapzen',
    url='https://github.com/thisisaaronland/py-mapzen-whosonfirst-export',
    install_requires=[
        'requests',
        'geojson',
        'shapely',
        'mapzen.whosonfirst.utils',
        ],
    dependency_links=[
        ],
    packages=packages,
    scripts=[
        'scripts/wof-exportify',
        ],
    download_url='https://github.com/mapzen/py-mapzen-whosonfirst-export/releases/tag/v0.55',
    license='BSD')
