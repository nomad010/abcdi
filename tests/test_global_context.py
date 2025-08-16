import unittest

from abcdi import set_context, context, get_dependency, call, bind_dependencies, Context
import abcdi


class TestGlobalContext(unittest.TestCase):
    def tearDown(self):
        abcdi._current_context = None

    def test_no_context_set_errors(self):
        with self.assertRaises(RuntimeError) as exception:
            context()
        self.assertEqual(
            str(exception.exception), 'No DI context is currently set. Use set_context() first.'
        )
        with self.assertRaises(RuntimeError) as exception:
            get_dependency('thing')
        self.assertEqual(
            str(exception.exception), 'No DI context is currently set. Use set_context() first.'
        )
        with self.assertRaises(RuntimeError) as exception:
            call(lambda: 5)
        self.assertEqual(
            str(exception.exception), 'No DI context is currently set. Use set_context() first.'
        )
        with self.assertRaises(RuntimeError) as exception:
            bind_dependencies(lambda: 5)
        self.assertEqual(
            str(exception.exception), 'No DI context is currently set. Use set_context() first.'
        )

    def test_context_set_twice_errors(self):
        set_context(Context(dependencies={}))
        with self.assertRaises(RuntimeError) as exception:
            set_context(Context(dependencies={}))
        self.assertEqual(
            str(exception.exception), 'DI context is already set for the application.'
        )

    def test_context_set_works(self):
        def func1(item, *, a, b):
            if item == 5 and a == 1 and b == 2:
                return 1

        test_context = Context(dependencies={
            'a': (int, [1], {})
        })
        set_context(test_context)
        self.assertEqual(context(), test_context)
        self.assertEqual(get_dependency('a'), 1)
        self.assertEqual(call(func1, 5, b=2), 1)

        @bind_dependencies
        def func2(item, *, a, b):
            if item == 6 and a == 1 and b == 4:
                return 2
        self.assertEqual(func2(6, b=4), 2)
