import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


VERSION = '0.4.1'


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='pyintercept',
    version=VERSION,
    description="Intercept function calls from Python scripts",
    author="Caio Ariede",
    author_email="caio.ariede@gmail.com",
    url="http://github.com/caioariede/pyintercept",
    license="MIT",
    zip_safe=False,
    platforms=["any"],
    packages=find_packages(),
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],
    include_package_data=True,
    install_requires=[
        'byteplay',
    ],
    tests_require=[
        'pytest',
    ],
    test_suite='py.test',
    cmdclass={'test': PyTest},
)
