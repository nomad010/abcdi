import unittest

from abcdi import Context, injectable


class TestInjected(unittest.TestCase):
    def test_empty_context_empty_function_succeeds(self):
        @injectable
        def dummy_function():
            return 5

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                _ = Context(dependencies={}, **kwargs)
                self.assertEqual(dummy_function(), 5)

    def test_empty_context_args_kwargs_function_succeeds(self):
        @injectable
        def dummy_function(a, *args, k=5, **kwargs):
            return a + sum(args) + k + sum(kwargs.values())

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                _ = Context(dependencies={}, **kwargs)
                self.assertEqual(dummy_function(1, 2, 3, 4, x=10), 25)

    def test_empty_context_invalid_function_call_errors_1(self):
        @injectable
        def dummy_function(a, *args, k=5, **kwargs):
            return a + sum(args) + k + sum(kwargs.values())

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                _ = Context(dependencies={}, **kwargs)

                with self.assertRaises(TypeError):
                    dummy_function()

    def test_empty_context_invalid_function_call_errors_2(self):
        @injectable
        def dummy_function(a, /, b, * c, d):
            pass

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                _ = Context(dependencies={}, **kwargs)

                with self.assertRaises(TypeError):
                    dummy_function()

                with self.assertRaises(TypeError):
                    dummy_function(1)

                with self.assertRaises(TypeError):
                    dummy_function(1, 2)

                with self.assertRaises(TypeError):
                    dummy_function(1, 2, c=3)
                
                with self.assertRaises(TypeError):
                    dummy_function(1, 2, 3)

    def test_dependency_successful_inject_1(self):
        @injectable
        def dummy_function(a, *, b):
            return a == 0 and b == 1

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': (int, [], {}),
                    'b': (int, [1], {}),
                    'c': (int, [2], {}),
                }, **kwargs)

                self.assertTrue(dummy_function(context.injected('a'), b=context.injected()))
                self.assertFalse(dummy_function(context.injected('a'), b=context.injected('c')))

    def test_dependency_successful_inject_2(self):
        class Dummy:
            @injectable
            def dummy_method(self, a, *, b):
                return a == 0 and b == 1
            
            @classmethod
            @injectable
            def dummy_cls_method(cls, a, *, b):
                return a == 0 and b == 1

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': (int, [], {}),
                    'b': (int, [1], {}),
                    'c': (int, [2], {}),
                    'self': (str, [], {})
                }, **kwargs)

                self.assertTrue(Dummy().dummy_method(context.injected('a'), b=context.injected()))
                self.assertFalse(Dummy().dummy_method(context.injected('a'), b=context.injected('c')))
                self.assertTrue(Dummy.dummy_cls_method(context.injected('a'), b=context.injected()))
                self.assertFalse(Dummy.dummy_cls_method(context.injected('a'), b=context.injected('c')))

    
    def test_dependency_name_not_given_arg_errors(self):
        @injectable
        def dummy_function(a):
            return a == 0

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': (int, [], {}),
                }, **kwargs)

                with self.assertRaises(RuntimeError) as exception:
                    dummy_function(context.injected())
                self.assertEqual(
                    str(exception.exception),
                    'Positional arguments require the dependency name to be passed to inject()'
                )

                with self.assertRaises(RuntimeError) as exception:
                    dummy_function(context.injected())
                self.assertEqual(
                    str(exception.exception),
                    'Positional arguments require the dependency name to be passed to inject()'
                )
