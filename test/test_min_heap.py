import unittest

from util.heap import MinHeap


class MinHeapTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.min_heap = MinHeap[int]()

    def test_min_always_top(self) -> None:
        for i in range(100_000, -1, -1):
            self.min_heap.push(i)
            self.assertEqual(self.min_heap.min, i)

        for i in range(100_000):
            self.assertEqual(self.min_heap.pop(), i)


if __name__ == "__main__":
    unittest.main()
