#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages()
desc = open("README.md").read(),

setup(
    name='mapzen.whosonfirst.export',
    namespace_packages=['mapzen', 'mapzen.whosonfirst', 'mapzen.whosonfirst.export'],
    version='0.4',
    description='Simple Python wrapper for managing Who\'s On First export-related functions',
    author='Mapzen',
    url='https://github.com/thisisaaronland/py-mapzen-whosonfirst-export',
    install_requires=[
        'requests',
        'geojson',
        'woe.isthat',
        # 'address_normalizer',
        'mapzen.whosonfirst.utils',
        ],
    dependency_links=[
        # 'https://github.com/openvenues/address_normalizer/tarball/master#egg=address-normalizer-0.2',
        'https://github.com/thisisaaronland/py-woe-isthat/tarball/master#egg=woe-isthat-0.15',
        'https://github.com/mapzen/py-mapzen-whosonfirst-utils/tarball/master#egg=mapzen-whosonfirst-utils-0.20',
        ],
    packages=packages,
    scripts=[
        'scripts/wof-concordify',
        ],
    download_url='https://github.com/mapzen/py-mapzen-whosonfirst-export/releases/tag/v0.4',
    license='BSD')
