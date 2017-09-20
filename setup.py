#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

# from distutils.core import setup
#from distutils.extension import Extension

from setuptools import setup, find_packages

from Cython.Distutils import build_ext
from Cython.Build import cythonize

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Cython',
    'numpy',
#    'Click>=6.0',
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest',
]

setup(
    name='totaldepth',
    version='0.1.0',
    description="TotalDepth is a software collection that can process petrophysical data such as wireline logs and seismic data.",
    long_description=readme + '\n\n' + history,
    author="Paul Ross",
    author_email='apaulross@gmail.com',
    url='https://github.com/paulross/totaldepth',
    packages=find_packages(include=['src']),
    package_dir={'' : 'src'},
    entry_points={
        'console_scripts': [
            'totaldepth=totaldepth.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GPLv2",
    zip_safe=False,
    keywords='totaldepth',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
# 	cmdclass = {'build_ext': build_ext},
# 	ext_modules = [
#         Extension("TotalDepth.LIS.core.cRepCode",
#                   ["src/TotalDepth/LIS/core/cRepCode.pyx"]),
#         Extension("TotalDepth.LIS.core.cFrameSet",
#                   ["src/TotalDepth/LIS/core/cFrameSet.pyx"]),
# 	]
    ext_modules = cythonize("src/TotalDepth/LIS/core/*.pyx"),
)
