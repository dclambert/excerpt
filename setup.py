# -*- coding: utf-8 -*-
import re
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand
from setuptools import find_packages


INSTALL_REQUIRES = [
    'docopt',
]

TEST_REQUIRES = [
    'pytest',
]

with open("README.rst") as f:
    README = f.read().decode("utf8")

class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name='excerpt',
    version="0.1.0",
    description='A platform for generating dockerized mysql data extracts.',
    long_description=README,
    author='Troy de Freitas',
    url='https://github.com/dosemedia/hume',
    install_requires=INSTALL_REQUIRES,
    zip_safe=False,
    keywords='excerpt',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    py_modules=["excerpt"],
    entry_points={
        'console_scripts': [
            "excerpt = excerpt.cli:main"
        ]
    },
    tests_requires=TEST_REQUIRES,
    cmdclass={'test': PyTest}
)
