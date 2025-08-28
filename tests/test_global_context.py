import unittest

from abcdi import set_context, context, subcontext, get_dependency, call, bind_dependencies, injected, injectable, factory, instance
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
        set_context(dependencies={})
        with self.assertRaises(RuntimeError) as exception:
            set_context(dependencies={})
        self.assertEqual(
            str(exception.exception), 'DI context is already set for the application.'
        )

    def test_context_set_works(self):
        def func1(item, *, a, b):
            if item == 5 and a == 1 and b == 2:
                return 1

        set_context(dependencies={
            'a': factory(int, 1)
        })
        self.assertEqual(get_dependency('a'), 1)
        self.assertEqual(call(func1, 5, b=2), 1)

        @bind_dependencies
        def func2(item, *, a, b):
            if item == 6 and a == 1 and b == 4:
                return 2
        self.assertEqual(func2(6, b=4), 2)

    def test_context_injected_works(self):
        @injectable
        def func1(item, *, a, b):
            if item == 5 and a == 1 and b == 2:
                return 1

        set_context(dependencies={
            'a': factory(int, 2),
            'c': factory(int, 1),
        })
        self.assertEqual(func1(5, a=injected('c'), b=2), 1)

    def test_subcontext(self):
        class DepA:
            def __init__(self, *, b):
                self.b = b

            def __eq__(self, value):
                return self.b == value.b

        for lazy in [True, False, None]:
            kwargs = {} if lazy is None else {'lazy': lazy}
            for sublazy in [True, False, None]:
                subkwargs = {} if sublazy is None else {'lazy': sublazy}               
                with self.subTest(lazy=lazy, sublazy=sublazy):
                    try:
                        set_context(dependencies={'existing': instance(DepA(b=5))}, **kwargs)
                        subdependencies = {
                            'existing': instance(DepA(b=1)),
                        }
                        self.assertEqual(context().get_dependency('existing'), DepA(b=5))
                        with subcontext(dependencies=subdependencies, **subkwargs) as subctx:
                            self.assertEqual(context().get_dependency('existing'), DepA(b=1))
                            self.assertEqual(subctx.get_dependency('existing'), DepA(b=1))
                        self.assertEqual(context().get_dependency('existing'), DepA(b=5))
                    finally:
                        self.tearDown()

    def test_context_laziness(self):
        class DepA:
            def __init__(self, *, b):
                self.b = b

            def __eq__(self, value):
                return self.b == value.b

        for lazy in [True, False, None]:
            kwargs = {} if lazy is None else {'lazy': lazy}
            for sublazy in [True, False, None]:
                subkwargs = {} if sublazy is None else {'lazy': sublazy}
                with self.subTest(lazy=lazy, sublazy=sublazy):
                    try:
                        set_context(dependencies={'existing': factory(DepA, b=5)}, **kwargs)
                        if lazy is True:
                            self.assertEqual(len(context().dependency_cache), 0)
                        else:
                            self.assertEqual(len(context().dependency_cache), 1)
                        subdependencies = {
                            'existing': factory(DepA, b=1),
                        }
                        with subcontext(dependencies=subdependencies, **subkwargs) as subctx:
                            if sublazy is True:
                                self.assertEqual(len(subctx.dependency_cache), 0)
                            else:
                                self.assertEqual(len(subctx.dependency_cache), 1)
                    finally:
                        self.tearDown()

    def test_injected_no_context(self):
        @injectable
        def fn(b = injected()):
            return b == 5
        
        with self.assertRaises(RuntimeError) as exception:
            self.assertTrue(fn())
        self.assertEqual(str(exception.exception), 'No DI context is currently set. Use set_context() first.')
    
    def test_injected_no_context_with_later_context(self):
        @injectable
        def fn(b = injected()):
            return b == 5
        for lazy in [True, False, None]:
            kwargs = {} if lazy is None else {'lazy': lazy}
            with self.subTest(lazy=lazy):
                set_context(dependencies={'b': instance(5)}, **kwargs)

                self.assertTrue(fn())
                self.tearDown()

    def test_injected_no_context_with_later_context_and_separate_context(self):
        for lazy in [True, False, None]:
            kwargs = {} if lazy is None else {'lazy': lazy}
            for sublazy in [True, False, None]:
                subkwargs = {} if sublazy is None else {'lazy': sublazy}
                with self.subTest(lazy=lazy, sublazy=sublazy):
                    set_context(dependencies={'b': instance(5)}, **kwargs)
                    ctx = abcdi.Context(dependencies={'c': instance(10)}, **subkwargs)

                    @injectable
                    def fn(b=injected(), c=ctx.injected()):
                        return b == 5 and c == 10

                    self.assertTrue(fn())
                    self.tearDown()

    def test_subcontext_creation_upward_hidden_errors(self):
        class DepA:
            def __init__(self, *, b):
                self.b = b

            def __eq__(self, value):
                return self.b == value.b
            
        class DepB:
            def __init__(self, *, existing):
                self.existing = existing

            def __eq__(self, value):
                return self.existing == value.existing

        for lazy in [True, False, None]:
            kwargs = {} if lazy is None else {'lazy': lazy}
            for sublazy in [False, None]:
                subkwargs = {} if sublazy is None else {'lazy': sublazy}               
                with self.subTest(lazy=lazy, sublazy=sublazy):
                    try:
                        set_context(dependencies={
                            'existing': factory(DepA, b=5),
                        }, **kwargs)
                        with self.assertRaises(TypeError) as exception:
                            subcontext(dependencies={
                                'subthing': factory(DepB),
                            }, hidden_dependencies={'existing'}, **subkwargs)
                        self.assertTrue(
                            str(exception.exception).endswith(
                                "DepB.__init__() missing 1 required keyword-only argument: 'existing'"
                            )
                        )
                    finally:
                        self.tearDown()
