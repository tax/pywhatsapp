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
    version='0.0.1',
    author='Paul Tax',
    author_email='paultax@gmail.com',
    include_package_data=True,
    install_requires=['yowsup2==2.3.167'],
    py_modules=['awsauth'],
    url='https://github.com/tax/python-requests-aws',
    license='BSD licence, see LICENCE.txt',
    description='Simple wrapper around yowsup to send a message or mediafile with whatsapp',
    long_description=open('README.md').read(),
)
