import pyintercept
import pytest

from pyintercept.lib import Patcher


def test_patch_file(capsys):
    p = Patcher()
    p.loads("""
from setuptools import setup
setup(package='foobar')
    """)
    p.patch_run(function='setuptools.setup', handler=pyintercept.print_)
    out, _err = capsys.readouterr()
    assert out == "()\n{'package': 'foobar'}\n"


def test_patch_file2(capsys):
    p = Patcher()
    p.loads("""
from setuptools import setup
setup(package='foo')
setup(package='bar')
    """)
    p.patch_run(function='setuptools.setup', handler=pyintercept.print_)
    out, _err = capsys.readouterr()
    assert out == "()\n{'package': 'foo'}\n()\n{'package': 'bar'}\n"


def test_patch_local_function(capsys):
    def double(origfn, i):
        print(i * 3)
    p = Patcher()
    p.loads("""
def double(i):
  print(i * 2)
double(1)
double(2)
    """)
    p.patch_run(function='double', handler=double)
    out, _err = capsys.readouterr()
    assert out == '3\n6\n'


def test_not_loaded():
    p = Patcher()
    with pytest.raises(AssertionError):
        p.patch_run(function='x')


def test_not_patched():
    p = Patcher()
    with pytest.raises(AssertionError):
        p.run()
    with pytest.raises(AssertionError):
        p.save('x.pyc')
