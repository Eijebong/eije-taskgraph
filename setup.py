import os
from distutils.util import convert_path

from setuptools import find_packages, setup

setup(
    name="mozilla-taskgraph",
    version="0.1.0",
    description="Eije's taskgrpah tranforms",
    url="https://github.com/Eijebong/eije-taskgraph",
    packages=find_packages("src"),
    package_dir={"": "src"},
)
