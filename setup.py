from setuptools import find_packages, setup

setup(
    name='sobiraka',
    version='0.0.1',
    author='Max Alibaev',
    python_requires='~=3.10',
    install_requires=[
        'aiofiles~=23.1.0',
        'utilspie~=0.1.0',
        'jinja2~=3.1.2',
        'jsonschema~=4.17.3',
        'more-itertools~=9.0.0',
        'panflute~=2.2.3',
        'pyyaml~=6.0',
    ],
    packages=find_packages('src'),
    package_dir={'sobiraka': 'src/sobiraka'},
    package_data={'sobiraka': ['files/**']},
    entry_points={
        'console_scripts': ['sobiraka=sobiraka.__main__:main'],
    },
)
