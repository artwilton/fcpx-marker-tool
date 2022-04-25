from setuptools import setup, find_packages

setup(
    name='fcpx-marker-tool',
    version='2.0.0',
    description='This package allows for parsing, displaying, and saving marker metadata from .fcpxml files.',
    author='Arthur Wilton',
    url='https://github.com/artwilton/fcpx-marker-tool',
    install_requires=['timecode'],
    packages=find_packages(exclude=('tests')),
    entry_points={
        'console_scripts' : [
            'fcpx-marker-tool = fcpx_marker_tool.main:main',
        ],
    },
)