import unittest
import pathlib

from abcdi import Context, factory, instance
from abcdi.context import _get_callable_parameters


class TestGetCallableParameters(unittest.TestCase):
    def test_get_no_constructor_parameters(self):
        class Constructor:
            pass
        self.assertEqual(_get_callable_parameters(Constructor), ['args', 'kwargs'])

    def test_get_constructor_parameters_1(self):
        class Constructor:
            def __init__(self, a):
                pass
        self.assertEqual(_get_callable_parameters(Constructor), ['a'])

    def test_get_constructor_parameters_2(self):
        class Constructor:
            def __init__(self, k=4):
                pass
        self.assertEqual(_get_callable_parameters(Constructor), ['k'])

    def test_get_constructor_parameters_3(self):
        class Constructor:
            def __init__(self, a, k=4):
                pass
        self.assertEqual(_get_callable_parameters(Constructor), ['a', 'k'])

    def test_get_function_parameters1(self):
        def fn():
            pass
        self.assertEqual(_get_callable_parameters(fn), [])

    def test_get_function_parameters_2(self):
        def fn(a):
            pass
        self.assertEqual(_get_callable_parameters(fn), ['a'])

    def test_get_function_parameters_3(self):
        def fn(k=4):
            pass
        self.assertEqual(_get_callable_parameters(fn), ['k'])

    def test_get_function_parameters_4(self):
        def fn(a, k=4):
            pass
        self.assertEqual(_get_callable_parameters(fn), ['a', 'k'])

    def test_get_function_parameters_5(self):
        def fn(self, a, k=4):
            pass
        self.assertEqual(_get_callable_parameters(fn), ['self', 'a', 'k'])

    def test_get_method_parameters_1(self):
        class Cls:
            def fn(self):
                pass
        self.assertEqual(_get_callable_parameters(Cls().fn), [])

    def test_get_method_parameters_2(self):
        class Cls:
            def fn(self, a):
                pass
        self.assertEqual(_get_callable_parameters(Cls().fn), ['a'])

    def test_get_method_parameters_3(self):
        class Cls:
            def fn(self, k=5):
                pass
        self.assertEqual(_get_callable_parameters(Cls().fn), ['k'])

    def test_get_method_parameters_4(self):
        class Cls:
            def fn(self, a, k=5):
                pass
        self.assertEqual(_get_callable_parameters(Cls().fn), ['a', 'k'])

    def test_get_lambda_parameters_1(self):
        self.assertEqual(_get_callable_parameters(lambda: 5), [])

    def test_get_lambda_parameters_2(self):
        self.assertEqual(_get_callable_parameters(lambda a: 5), ['a'])

    def test_get_lambda_parameters_3(self):
        self.assertEqual(_get_callable_parameters(lambda k=2: 5), ['k'])

    def test_get_lambda_parameters_4(self):
        self.assertEqual(_get_callable_parameters(lambda a, k=2: 5), ['a', 'k'])

    def test_get_method_property(self):
        class Cls:
            @property
            def fn(self):
                pass

        with self.assertRaises(TypeError):
            _get_callable_parameters(Cls().fn)

    def test_get_method_stored_with_on_object_1(self):
        def x():
            pass

        class Cls:
            def __init__(self, a):
                self.a = a

        self.assertEqual(_get_callable_parameters(Cls(x).a), [])

    def test_get_method_stored_with_on_object_2(self):
        def x(a):
            pass

        class Cls:
            def __init__(self, a):
                self.a = a

        self.assertEqual(_get_callable_parameters(Cls(x).a), ['a'])

    def test_get_method_stored_with_on_object_3(self):
        def x(k=5):
            pass

        class Cls:
            def __init__(self, a):
                self.a = a

        self.assertEqual(_get_callable_parameters(Cls(x).a), ['k'])

    def test_get_method_stored_with_on_object_4(self):
        def x(a, k=4):
            pass

        class Cls:
            def __init__(self, a):
                self.a = a

        self.assertEqual(_get_callable_parameters(Cls(x).a), ['a', 'k'])


class TestContext(unittest.TestCase):
    def test_empty_create_succeeds(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={}, **kwargs)
                self.assertDictEqual(context.dependency_cache, {})

    def test_create_with_simple_type_default_constructor_1(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'test_int': factory(int)
                }, **kwargs)
                if lazy:
                    self.assertDictEqual(context.dependency_cache, {})
                else:
                    self.assertDictEqual(context.dependency_cache, {'test_int': 0})
                self.assertEqual(context.get_dependency('test_int'), 0)
                self.assertDictEqual(context.dependency_cache, {'test_int': 0})

    def test_create_with_simple_type_default_constructor_2(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'test_str': factory(str)
                }, **kwargs)
                if lazy:
                    self.assertDictEqual(context.dependency_cache, {})
                else:
                    self.assertDictEqual(context.dependency_cache, {'test_str': ''})
                self.assertEqual(context.get_dependency('test_str'), '')
                self.assertDictEqual(context.dependency_cache, {'test_str': ''})

    def test_create_with_simple_type_args_1(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'test_int': factory(int, 1)
                }, **kwargs)
                if lazy:
                    self.assertDictEqual(context.dependency_cache, {})
                else:
                    self.assertDictEqual(context.dependency_cache, {'test_int': 1})
                self.assertEqual(context.get_dependency('test_int'), 1)
                self.assertDictEqual(context.dependency_cache, {'test_int': 1})

    def test_create_with_simple_type_args_2(self):
        for lazy in [True, False, None]:
            kwargs = {} if lazy is None else {'lazy': lazy}
            with self.subTest(lazy=lazy):
                context = Context(dependencies={
                    'test_str': factory(str, 1)
                }, **kwargs)
                if lazy:
                    self.assertDictEqual(context.dependency_cache, {})
                else:
                    self.assertDictEqual(context.dependency_cache, {'test_str': '1'})
                self.assertEqual(context.get_dependency('test_str'), '1')
                self.assertDictEqual(context.dependency_cache, {'test_str': '1'})

    def test_create_with_simple_type_kwargs_1(self):
        class Kwargs:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def __eq__(self, value):
                return self.kwargs == value.kwargs

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'test_kwargs': factory(Kwargs, a=1)
                }, **kwargs)
                if lazy:
                    self.assertDictEqual(context.dependency_cache, {})
                else:
                    self.assertDictEqual(context.dependency_cache, {'test_kwargs': Kwargs(a=1)})
                self.assertEqual(context.get_dependency('test_kwargs'), Kwargs(a=1))
                self.assertDictEqual(context.dependency_cache, {'test_kwargs': Kwargs(a=1)})

    def test_create_with_simple_type_args_and_kwargs_1(self):
        class ArgsAndKwargs:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def __eq__(self, value):
                return self.args == value.args and self.kwargs == value.kwargs

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'test_args': factory(ArgsAndKwargs, 'b', a=1)
                }, **kwargs)
                if lazy:
                    self.assertDictEqual(context.dependency_cache, {})
                else:
                    self.assertDictEqual(context.dependency_cache, {'test_args': ArgsAndKwargs('b', a=1)})
                self.assertEqual(context.get_dependency('test_args'), ArgsAndKwargs('b', a=1))
                self.assertDictEqual(context.dependency_cache, {'test_args': ArgsAndKwargs('b', a=1)})

    def test_create_incorrect_factory_type_1(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': factory(5)}, **kwargs)
                self.assertEqual(
                    str(exception.exception), 'Factory class for test_args must be a type'
                )

    def test_create_incorrect_factory_type_2(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': 6}, **kwargs)
                self.assertEqual(
                    str(exception.exception),
                    'Dependency test_args must be a config dict from factory() or instance()'
                )

    def test_create_incorrect_factory_type_3(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {}}, **kwargs)
                self.assertEqual(
                    str(exception.exception),
                    'Dependency test_args config dict must have \'type\' field'
                )

    def test_create_incorrect_factory_type_4(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {
                        'type': 'unknown'
                    }}, **kwargs)
                self.assertEqual(
                    str(exception.exception),
                    'Unknown dependency type \'unknown\' for test_args'
                )

    def test_create_incorrect_factory_type_5(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {
                        'type': 'factory'
                    }}, **kwargs)
                self.assertEqual(
                    str(exception.exception),
                    'Factory class for test_args must be a type'
                )

    def test_create_incorrect_factory_type_6(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {
                        'type': 'factory',
                        'class': 5
                    }}, **kwargs)
                self.assertEqual(
                    str(exception.exception), 'Factory class for test_args must be a type'
                )

    def test_create_incorrect_factory_type_7(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {
                        'type': 'factory',
                        'class': int,
                        'args': 5
                    }}, **kwargs)
                self.assertEqual(
                    str(exception.exception), 'Factory args for test_args must be a list'
                )

    def test_create_incorrect_factory_type_8(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {
                        'type': 'factory',
                        'class': int,
                        'args': [6],
                        'kwargs': 5
                    }}, **kwargs)
                self.assertEqual(
                    str(exception.exception), 'Factory kwargs for test_args must be a dict'
                )

    def test_create_incorrect_factory_type_9(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {
                        'type': 'instance',
                    }}, **kwargs)
                self.assertEqual(
                    str(exception.exception), 'Instance config for test_args must have \'value\' field'
                )
    
    def test_create_incorrect_factory_type_10(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    Context(dependencies={'test_args': {
                        'type': 'factory',
                        'class': int,
                        'args': [5]
                    }}, **kwargs)
                self.assertEqual(
                    str(exception.exception), 'Factory kwargs for test_args must be a dict'
                )

    def test_missing_dependency_raises_key_error(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'test_found': factory(str)
                }, **kwargs)
                with self.assertRaises(KeyError) as exception:
                    context.get_dependency('test_missing')
                self.assertEqual(
                    str(exception.exception),
                    "\"Dependency 'test_missing' is not registered in this context or parent contexts\""
                )

    def test_call_for_empty_context_works(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={}, **kwargs)

                def test_call():
                    return 'works'
                self.assertEqual(context.call(test_call), 'works')

    def test_args_call_for_empty_context_works(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={}, **kwargs)

                def test_call(a, b, c, d, e):
                    if (a, b, c, d, e) == (1, 2, 3, 4, 5):
                        return 'works'
                self.assertEqual(context.call(test_call, 1, 2, 3, 4, 5), 'works')

    def test_kwargs_call_for_empty_context_works(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={}, **kwargs)

                def test_call(a=1, b=2, c=0, d=4, e=5):
                    if (a, b, c, d, e) == (1, 2, 3, 4, 5):
                        return 'works'
                self.assertEqual(context.call(test_call, c=3), 'works')

    def test_args_kwargs_call_for_empty_context_works(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={}, **kwargs)

                def test_call(x, y, z, a=1, b=2, c=0, d=4, e=5):
                    if (x, y, z, a, b, c, d, e) == (1, 2, 3, 1, 2, 3, 4, 5):
                        return 'works'
                self.assertEqual(context.call(test_call, 1, 2, 3, c=3), 'works')

    def test_simple_context_call(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': factory(int, 1000),
                    'b': factory(int, 2000),
                    'c': factory(int, 3000),
                    'd': factory(int, 4000),
                    'e': factory(int, 5000),
                }, **kwargs)

                def test_call(a=1, b=2, c=0, d=4, e=5):
                    if (a, b, c, d, e) == (1000, 2000, 3000, 4000, 5000):
                        return 'works'
                self.assertEqual(context.call(test_call), 'works')

    def test_simple_context_call_overriden_by_kwargs(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': factory(int, 1000),
                    'b': factory(int, 2000),
                    'c': factory(int, 3000),
                    'd': factory(int, 4000),
                    'e': factory(int, 5000),
                }, **kwargs)

                def test_call(a=1, b=2, c=0, d=4, e=5):
                    if (a, b, c, d, e) == (-1, 2000, -3, 4000, -5):
                        return 'works'
                self.assertEqual(context.call(test_call, a=-1, c=-3, e=-5), 'works')

    def test_args_kwargs_call_for_unrelated_context_works(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'first': factory(str, 1),
                    'second': factory(str, 2),
                    'third': factory(str, 3),
                }, **kwargs)

                def test_call(x, y, z, a=1, b=2, c=0, d=4, e=5):
                    if (x, y, z, a, b, c, d, e) == (1, 2, 3, 1, 2, 3, 4, 5):
                        return 'works'
                self.assertEqual(context.call(test_call, 1, 2, 3, c=3), 'works')

    def test_context_bind_decorator_works(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'path': factory(pathlib.Path, 'file.txt'),
                }, **kwargs)

                @context.bind_dependencies
                def test_call(path):
                    if str(path) == 'file.txt':
                        return 'works'
                self.assertEqual(test_call(), 'works')

    def test_context_bind_inline_works(self):
        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'path': factory(pathlib.Path, 'file.txt'),
                }, **kwargs)

                def test_call(path):
                    if str(path) == 'file.txt':
                        return 'works'
                self.assertEqual(context.bind_dependencies(test_call)(), 'works')

    def test_context_complicated_chain_works_1(self):
        class DepA:
            def __init__(self, *, b, c):
                self.b = b
                self.c = c

            def __eq__(self, value):
                return self.b == value.b and self.c == value.c

        class DepB:
            def __init__(self, *, c):
                self.c = c

            def __eq__(self, value):
                return self.c == value.c

        class DepC:
            def __init__(self, *, b):
                self.b = b

            def __eq__(self, value):
                return self.b == value.b

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': factory(DepA),
                    'b': factory(DepB),
                    'c': factory(DepC, b=5),
                }, **kwargs)
                c = DepC(b=5)
                b = DepB(c=c)
                a = DepA(b=b, c=c)
                self.assertEqual(context.get_dependency('a'), a)

    def test_context_circular_dependency_detected_1(self):
        class DepA:
            def __init__(self, *, b):
                self.b = b

        class DepB:
            def __init__(self, *, a):
                self.a = a

        with self.subTest(lazy=True):
            context = Context(dependencies={
                'a': factory(DepA),
                'b': factory(DepB),
            }, lazy=True)
            with self.assertRaises(ValueError) as exception:
                context.get_dependency('a')
            self.assertEqual(str(exception.exception), 'Circular dependency detected: a -> b -> a')
            with self.assertRaises(ValueError) as exception:
                context.get_dependency('b')
            self.assertEqual(str(exception.exception), 'Circular dependency detected: b -> a -> b')

        for lazy in [False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                with self.assertRaises(ValueError) as exception:
                    context = Context(dependencies={
                        'a': factory(DepA),
                        'b': factory(DepB),
                    }, **kwargs)
                self.assertEqual(str(exception.exception), 'Circular dependency detected: a -> b -> a')

    def test_dependency_with_args_works(self):
        class DepA:
            def __init__(self, b, c):
                self.b = b
                self.c = c

            def __eq__(self, value):
                return self.b == value.b and self.c == value.c

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': factory(DepA, 1, 2),
                }, **kwargs)
                self.assertEqual(context.get_dependency('a'), DepA(1, 2))

    def test_instance_dependency_works(self):
        class DepA:
            def __init__(self, *, b):
                self.b = b

            def __eq__(self, value):
                return self.b == value.b

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'a': instance(DepA(b=5)),
                }, **kwargs)
                self.assertEqual(context.get_dependency('a'), DepA(b=5))
                self.assertDictEqual(context.dependency_cache, {'a': DepA(b=5)})

    def test_has_dependency_works(self):
        class DepA:
            def __init__(self, *, b):
                self.b = b

            def __eq__(self, value):
                return self.b == value.b

        for lazy in [True, False, None]:
            with self.subTest(lazy=lazy):
                kwargs = {} if lazy is None else {'lazy': lazy}
                context = Context(dependencies={
                    'existing': instance(DepA(b=5)),
                }, **kwargs)
                self.assertTrue(context.has_dependency('existing'))
                self.assertFalse(context.has_dependency('notexisting'))

    def test_subcontext_has_dependency_works(self):
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
                    context = Context(dependencies={
                        'existing': instance(DepA(b=5)),
                    }, **kwargs)
                    subcontext = context.subcontext(dependencies={
                        'onlysubcontext': instance(DepA(b=5)),
                    }, **subkwargs)
                    self.assertTrue(context.has_dependency('existing'))
                    self.assertFalse(context.has_dependency('notexisting'))
                    self.assertFalse(context.has_dependency('onlysubcontext'))
                    self.assertTrue(subcontext.has_dependency('existing'))
                    self.assertFalse(subcontext.has_dependency('notexisting'))
                    self.assertTrue(subcontext.has_dependency('onlysubcontext'))

    def test_subcontext_get_dependency_works(self):
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
                    context = Context(dependencies={
                        'existing': instance(DepA(b=5)),
                    }, **kwargs)
                    subcontext = context.subcontext(dependencies={
                        'onlysubcontext': instance(DepA(b=1)),
                    }, **subkwargs)
                    self.assertEqual(context.get_dependency('existing'), DepA(b=5)) 
                    with self.assertRaises(KeyError) as exception:
                        context.get_dependency('notexisting')
                    self.assertEqual(
                        str(exception.exception),
                        "\"Dependency 'notexisting' is not registered in this context or parent contexts\""
                    )
                    with self.assertRaises(KeyError) as exception:
                        context.get_dependency('onlysubcontext')
                    self.assertEqual(
                        str(exception.exception),
                        "\"Dependency 'onlysubcontext' is not registered in this context or parent contexts\""
                    )
                    self.assertEqual(subcontext.get_dependency('existing'), DepA(b=5))
                    with self.assertRaises(KeyError) as exception:
                        subcontext.get_dependency('notexisting')
                    self.assertEqual(
                        str(exception.exception),
                        "\"Dependency 'notexisting' is not registered in this context or parent contexts\""
                    )
                    self.assertEqual(subcontext.get_dependency('onlysubcontext'), DepA(b=1))

    def test_subcontext_shadowing_works(self):
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
                    context = Context(dependencies={
                        'existing': instance(DepA(b=5)),
                    }, **kwargs)
                    subcontext = context.subcontext(dependencies={
                        'existing': instance(DepA(b=1)),
                    }, **subkwargs)
                    self.assertEqual(context.get_dependency('existing'), DepA(b=5))
                    self.assertEqual(subcontext.get_dependency('existing'), DepA(b=1))


    def test_subcontext_creation_upward_works(self):
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
            for sublazy in [True, False, None]:
                subkwargs = {} if sublazy is None else {'lazy': sublazy}               
                with self.subTest(lazy=lazy, sublazy=sublazy):
                    context = Context(dependencies={
                        'existing': factory(DepA, b=5),
                    }, **kwargs)
                    subcontext = context.subcontext(dependencies={
                        'subthing': factory(DepB),
                    }, **subkwargs)
                    self.assertEqual(
                        subcontext.get_dependency('subthing'),
                        DepB(existing=DepA(b=5))
                    )
    
    def test_subcontext_creation_downward_errors(self):
        class DepA:
            def __init__(self, *, subthing):
                self.subthing = subthing

            def __eq__(self, value):
                return self.subthing == value.subthing
            
        class DepB:
            def __init__(self, *, existing):
                self.existing = existing

            def __eq__(self, value):
                return self.existing == value.existing

        for sublazy in [True, False, None]:
            subkwargs = {} if sublazy is None else {'lazy': sublazy}   
            with self.subTest(sublazy=sublazy):
                context = Context(dependencies={
                    'existing': factory(DepA, b=5),
                }, lazy=True)
                context.subcontext(dependencies={
                    'subthing': factory(DepB, existing=5),
                }, **subkwargs)
                with self.assertRaises(TypeError):
                    context.get_dependency('existing')

    def test_subcontext_context_manager(self):
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
                    context = Context(dependencies={
                        'existing': instance(DepA(b=5)),
                    }, **kwargs)
                    subdependencies = {
                        'onlysubcontext': instance(DepA(b=5)),
                    }
                    with context.subcontext(dependencies=subdependencies, **subkwargs) as subcontext:
                        self.assertTrue(context.has_dependency('existing'))
                        self.assertFalse(context.has_dependency('notexisting'))
                        self.assertFalse(context.has_dependency('onlysubcontext'))
                        self.assertTrue(subcontext.has_dependency('existing'))
                        self.assertFalse(subcontext.has_dependency('notexisting'))
                        self.assertTrue(subcontext.has_dependency('onlysubcontext'))

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
                    ctx = Context(dependencies={'existing': factory(DepA, b=5)}, **kwargs)
                    if lazy is True:
                        self.assertEqual(len(ctx.dependency_cache), 0)
                    else:
                        self.assertEqual(len(ctx.dependency_cache), 1)
                    subdependencies = {
                        'existing': factory(DepA, b=1),
                    }
                    with ctx.subcontext(dependencies=subdependencies, **subkwargs) as subctx:
                        if sublazy is True:
                            self.assertEqual(len(subctx.dependency_cache), 0)
                        else:
                            self.assertEqual(len(subctx.dependency_cache), 1)
