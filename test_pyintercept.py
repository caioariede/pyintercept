import pyintercept
import pytest
import uncompyle6

from pyintercept.lib import Patcher


def print_code(code):
    print(uncompyle6.deparse_code(2.7, code).text)


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


def test_patch_file_globals(capsys):
    p = Patcher()
    p.filepath = 'foo.py'
    p.loads("""
print(__file__)
from setuptools import setup
setup(package='foobar')
    """)
    p.patch_run(function='setuptools.setup', handler=pyintercept.print_)
    out, _err = capsys.readouterr()
    assert out == "foo.py\n()\n{'package': 'foobar'}\n"


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


def test_patch_multiple_calls(capsys):
    p = Patcher()
    p.loads("""
def x(*args):
    pass
x(1)
def foo(**kwargs):
    pass
foo(bar=2)
    """)
    p.patch(function='x', handler=pyintercept.print_)
    p.patch(function='foo', handler=pyintercept.print_)
    p.run()
    out, _err = capsys.readouterr()
    assert out == "(1,)\n{}\n()\n{'bar': 2}\n"


def test_patch_all_calls(capsys):
    p = Patcher()
    p.loads("""
def x(*args):
    pass
x(1)
def foo(**kwargs):
    pass
foo(bar=2)
    """)
    p.patch(handler=pyintercept.print_)
    p.run()
    out, _err = capsys.readouterr()
    assert out == "(1,)\n{}\n()\n{'bar': 2}\n"


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
