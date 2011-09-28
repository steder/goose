import os

from setuptools import setup

requirements = ["argparse",
                "pyyaml",
                "sqlalchemy>=0.6.6",
                ]
test_requirements = ["nose",
                     ]

root = os.path.dirname(__file__)

def long_description():
    readme = os.path.join(root, "README.rst")
    long_description = open(readme, "r").read()
    return long_description

def version():
    init = os.path.join(root, "goose", "__init__.py")
    version = None
    for line in open(init, "r"):
        if line.startswith("__version__"):
            version = line.split("=")[-1].strip().replace('\"', '')
    assert version is not None, "Unable to determine version!"
    return version

setup(name="Goose",
      version=version(),
      description='Basic SQL migration tool favoring configuration over convention.',
      long_description=long_description(),
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Topic :: Software Development',
                   'Topic :: Database',
                   'Topic :: Utilities'],
      author='Mike Steder',
      author_email='steder@gmail.com',
      url='https://bitbucket.org/steder/goose',
      packages=['goose'],
      scripts=["bin/goose"],
      install_requires=requirements,
      tests_require=test_requirements,
      test_suite="goose",
     )
