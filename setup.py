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
    packages=find_packages('src'),
    package_dir={'sobiraka': 'src/sobiraka'},
    entry_points={
        'console_scripts': ['sobiraka=sobiraka.__main__:main'],
    },
)
