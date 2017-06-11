#
# Copyright 2017 Cian Montgomery
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

import os
import subprocess

from setuptools import setup, Extension, find_packages

setup(
    name='cyst',
    version='0.0.1',
    description='Sawtooth continuous integration status tool',
    author='Cian Montgomery',
    url='https://github.com/cianx/sawtooth-utils',
    packages=find_packages(),
    install_requires=[
        "PyGithub>=1.34",
        "python-jenkins>=0.4.14"
    ],
    entry_points={
        'console_scripts': [
            'cyst = cyst.cyst:main_wrapper'
        ]
    })
