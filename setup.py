# -*- coding: utf-8 -*-
import os
import sys

try:
    from setuptools import setup
    # hush pyflakes
    setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='pywhatsapp',
    version='0.0.7',
    author='Paul Tax',
    author_email='paultax@gmail.com',
    include_package_data=True,
    install_requires=['yowsup2==2.5.0'],
    py_modules=['whatsapp'],
    url='https://github.com/tax/pywhatsapp',
    license='BSD licence, see LICENCE.txt',
    description='Simple wrapper around yowsup to send a message or mediafile with whatsapp',
    long_description=open('README.md').read(),
)
