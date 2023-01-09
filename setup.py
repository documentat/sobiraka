#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='sobiraka',
    version='0.0.1',
    author='Max Alibaev',
    python_requires='~=3.11',
    install_requires=[
        'panflute~=2.2.3',
        'pyyaml~=6.0',
    ],
    packages=find_packages(where='src'),
    package_dir={
        '': 'src',
    },
    entry_points={
        'console_scripts': ['sobiraka=sobiraka.main:main'],
    },
)
