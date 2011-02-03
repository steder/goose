#!/usr/bin/env python

from distutils.core import setup


requirements = ["argparse",
                "pyyaml",
                "sqlalchemy>=0.6.6",
                ]


setup(name="Goose",
      version="1.0",
      description='Python Distribution Utilities',
      author='Mike Steder',
      author_email='steder@gmail.com',
      url='https://bitbucket.org/steder/goose',
      packages=['goose'],
      scripts=["bin/goose"],
      install_requires=requirements,
     )
