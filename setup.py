#!/usr/bin/env python

from distutils.core import setup

from setuptools import find_packages

setup(
    name='sobiraka',
    version='0.0.1',
    author='Max Alibaev',
    python_requires='~=3.11',
    install_requires=[
        'panflute>=2.2.3,<2.3'
        'pyyaml>=5.3.1<5.4',
    ],
    packages=find_packages(where='src'),
    package_dir={
        '': 'src',
    },
    entry_points={
        'sobiraka': ['christ=sobiraka:main'],
    },
)
