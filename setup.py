#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages()
desc = open("README.md").read(),

setup(
    name='mapzen.whosonfirst.export',
    namespace_packages=['mapzen', 'mapzen.whosonfirst', 'mapzen.whosonfirst.export'],
    version='0.6',
    description='Simple Python wrapper for managing Who\'s On First export-related functions',
    author='Mapzen',
    url='https://github.com/thisisaaronland/py-mapzen-whosonfirst-export',
    install_requires=[
        'requests',
        'geojson',
        'shapely',
        'atomicwrites',
        'mapzen.whosonfirst.utils>=0.05',
        'mapzen.whosonfirst.geojson>=0.03',
        'mapzen.whosonfirst.validator>=0.04',
        ],
    dependency_links=[
        'https://github.com/whosonfirst/py-mapzen-whosonfirst-utils/tarball/master#egg=mapzen.whosonfirst.utils',
        'https://github.com/whosonfirst/py-mapzen-whosonfirst-geojson/tarball/master#egg=mapzen.whosonfirst.geojson',
        'https://github.com/whosonfirst/py-mapzen-whosonfirst-validator/tarball/master#egg=mapzen.whosonfirst.validator',
        ],
    packages=packages,
    scripts=[
        'scripts/wof-exportify',
        ],
    download_url='https://github.com/mapzen/py-mapzen-whosonfirst-export/releases/tag/v0.6',
    license='BSD')
