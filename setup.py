import os
from distutils.util import convert_path

from setuptools import find_packages, setup

setup(
    name="eije_taskgraph",
    version="0.1.0",
    description="Eije's taskgraph tranforms",
    url="https://github.com/Eijebong/eije-taskgraph",
    packages=find_packages("src"),
    package_dir={"": "src"},
)
