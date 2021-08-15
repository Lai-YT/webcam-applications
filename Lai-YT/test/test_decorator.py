# run test with command under the parent directories of /test/:
# python -m unittest -v test.test_decorator

import unittest
from typing import Any, List

from lib.decorator import pass_by_copy


def foo_no_decor(list: List[Any]) -> None:
    list.append('foo')

@pass_by_copy(pos=[0])
def foo_pos_decor(list: List[Any]) -> None:
    list.append('foo')

@pass_by_copy(kw=['list'])
def foo_kw_decor(list: List[Any]) -> None:
    list.append('foo')

@pass_by_copy(pos=[0, 1])
def foo_multi_arg(list_1: List[Any], list_2: List[Any]) -> None:
    list_1.append('foo')
    list_2.append('foo')

@pass_by_copy(pos=[0, 0, 0])
def foo_duplicate_pos_decor(list: List[Any]) -> None:
    list.append('foo')

@pass_by_copy(pos=[0, 0, 0], kw=['list', 'list'])
def foo_duplicate_pos_kw_decor(list: List[Any]) -> None:
    list.append('foo')

@pass_by_copy(pos=[0])
def bar(list: List[List[Any]]) -> None:
    """bar"""
    list[0].append('bar')


class CopyDecoratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.list = ['0', '1', '2']

    def test_pure_func(self) -> None:
        foo_no_decor(self.list)
        self.assertEqual(['0', '1', '2', 'foo'], self.list)

    def test_func_arg_pass_by_pos(self) -> None:
        foo_pos_decor(self.list)
        self.assertEqual(['0', '1', '2'], self.list)
        foo_kw_decor(self.list)
        self.assertEqual(['0', '1', '2'], self.list)

    def test_func_arg_pass_by_kw(self) -> None:
        foo_pos_decor(list=self.list)
        self.assertEqual(['0', '1', '2'], self.list)
        foo_kw_decor(list=self.list)
        self.assertEqual(['0', '1', '2'], self.list)

    def test_func_with_multi_arg(self) -> None:
        foo_multi_arg(self.list, self.list)
        self.assertEqual(['0', '1', '2'], self.list)

    def test_func_with_duplicate_decor_arg(self) -> None:
        foo_duplicate_pos_decor(self.list)
        self.assertEqual(['0', '1', '2'], self.list)
        foo_duplicate_pos_kw_decor(self.list)
        self.assertEqual(['0', '1', '2'], self.list)

    def test_deep_copy(self) -> None:
        list = [['0', '1', '2']]
        bar(list)
        self.assertEqual([['0', '1', '2']], list)

    def test_docstring(self) -> None:
        self.assertEqual('bar', bar.__doc__)


if __name__ == '__main__':
    unittest.main()
