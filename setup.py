from setuptools import find_packages, setup

setup(
    name='sobiraka',
    version='0.0.1',
    author='Max Alibaev',
    python_requires='~=3.11',
    install_requires=[
        'aiofiles~=23.1.0',
        'beautifulsoup4~=4.12.2',
        'checksumdir~=1.2.0',
        'clint~=0.5.1',
        'colorama~=0.4.6',
        'diskcache~=5.6.1',
        'gitpython~=3.1.30',
        'jinja2~=3.1.2',
        'jsonschema~=4.17.3',
        'more-itertools~=9.0.0',
        'panflute~=2.2.3',
        'pygments~=2.16.1',
        'python-iso639~=2023.6.15',
        'pyyaml~=6.0',
        'setuptools~=68.1.2',
        'utilspie~=0.1.0',
        'wcmatch~=8.4.1',
        'yattag~=1.15.1',
    ],
    packages=find_packages('src'),
    package_dir={'sobiraka': 'src/sobiraka'},
    package_data={'sobiraka': ['files/**']},
    entry_points={
        'console_scripts': ['sobiraka=sobiraka.__main__:main'],
    },
)
