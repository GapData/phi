import tensorflow as tf
from phi import ph, Builder
from fn import _
import math
# from phi import tb

add2 = _ + 2
mul3 = _ * 3
get_list = lambda x: [1,2,3]
a2_plus_b_minus_2c = lambda a, b, c: a ** 2 + b - 2*c


@Builder.register_1("test.lib")
def add(a, b):
    """Some docs"""
    return a + b

@Builder.register_2("test.lib")
def pow(a, b):
    return a ** b

@Builder.register_method("test.lib")
def get_function_name(self):
    return self._f.__name__

class DummyContext:
    def __init__(self, val):
        self.val = val

    def __enter__(self):
        return self.val
    def __exit__(self, type, value, traceback):
        pass


class TestBuilder(object):
    """docstring for TestBuilder"""

    @classmethod
    def setup_method(self):
        self.x = tf.placeholder(tf.float32, shape=[None, 5])

    def test_C_1(self):
        assert ph._1(add2)(4) == 6
        assert ph._1(add2)._1(mul3)(4) == 18

        assert ph.Compile(add2)(4) == 6
        assert ph.Compile(add2, mul3)(4) == 18

    def test_methods(self):
        assert 9 == ph.Pipe(
            "hello world !!!",
            ph.Obj.split(" ")
            .filter(ph.Obj.contains("wor").Not())
            .map(len),
            sum,
            _ + 0.5,
            round
        )

        assert not ph.Pipe(
            [1,2,3],
            ph.Obj.contains(5)
        )

        class A(object):
            def something(self, x):
                return "y" * x


        assert "yyy" == ph.Pipe(
            A(),
            ph.Obj.something(3) #used something
        )

    def test_rrshift(self):
        builder = ph.Compile(
            _ + 1,
            _ * 2,
            _ + 4
        )

        assert 10 == 2 >> builder

    def test_compose(self):
        f = ph.Compile(
            _ + 1,
            _ * 2,
            _ + 4
        )

        assert 10 == f(2)

    def test_compose_list(self):
        f = ph.Compile(
            _ + 1,
            _ * 2, {'x'},
            _ + 4,
            [
                _ + 2
            ,
                _ / 2
            ,
                'x'
            ]
        )

        assert [12, 5, 6] == f(2)

    def test_compose_list_reduce(self):
        f = ph.Compile(
            _ + 1,
            _ * 2,
            _ + 4,
            [
                _ + 2
            ,
                _ / 2
            ],
            sum
        )

        assert 17 == f(2)

    def test_random(self):

        assert 9 == ph.Pipe(
            "Hola Cesar",
            ph.Obj.split(" ")
            .map(len)
            .sum()
        )

    def test_0(self):
        from datetime import datetime
        import time

        t0 = datetime.now()

        time.sleep(0.01)

        t1 = 2 >> ph.Compile(
            _ + 1,
            ph._0(datetime.now)
        )

        assert t1 > t0

    def test_1(self):
        assert 9 == 2 >> ph.Compile(
            _ + 1,
            ph._1(math.pow, 2)
        )

    def test_2(self):
        assert [2, 4] == [1, 2, 3] >> ph.Compile(
            ph._2(map, _ + 1),
            ph._2(filter, _ % 2 == 0)
        )

        assert [2, 4] == ph.Pipe(
            [1, 2, 3],
            ph._2(map, _ + 1),
            ph._2(filter, _ % 2 == 0)
        )


    def test_underscores(self):
        assert ph._1(a2_plus_b_minus_2c, 2, 4)(3) == 3 # (3)^2 + 2 - 2*4
        assert ph._2(a2_plus_b_minus_2c, 2, 4)(3) == -1 # (2)^2 + 3 - 2*4
        assert ph._3(a2_plus_b_minus_2c, 2, 4)(3) == 2 # (2)^2 + 4 - 2*3

    def test_pipe(self):
        assert ph.Pipe(4, add2, mul3) == 18

        assert [18, 14] == ph.Pipe(
            4,
            [
            (
                add2,
                mul3
            )
            ,
            (
                mul3,
                add2
            )
            ]
        )

        assert [18, 18, 15, 16] == ph.Pipe(
            4,
            [
                (
                    add2,
                    mul3
                )
            ,
                [
                    (
                        add2,
                        mul3
                    )
                ,
                    (
                        mul3,
                        add2,
                        [
                            _ + 1,
                            _ + 2
                        ]
                    )
                ]
            ],
            flatten=True
        )

        assert [18, 18, 14, get_list(None)] == ph.Pipe(
            4,
            [
            (
                add2,
                mul3
            )
            ,
                [
                (
                    add2,
                    mul3
                )
                ,
                (
                    mul3,
                    add2
                )
                ,
                    get_list
                ]
            ]
        )

        [a, b, c] = ph.Pipe(
            4,
            [
                (
                add2,
                mul3
                )
            ,
                [
                    (
                    add2,
                    mul3
                    )
                ,
                    (
                    mul3,
                    add2
                    )
                ]
            ]
        )

        assert a == 18 and b == 18 and c == 14

    def test_scope(self):
        y = ph.ref('y')

        z = ph.Pipe(
            self.x,
            ph.With( tf.name_scope('TEST'),
            (
                _ * 2,
                _ + 4,
                { y }
            )),
            _ ** 3
        )

        assert "TEST/" in y().name
        assert "TEST/" not in z.name

    def test_register_1(self):

        #register
        assert 5 == ph.Pipe(
            3,
            ph.add(2)
        )

        #register_2
        assert 8 == ph.Pipe(
            3,
            ph.pow(2)
        )

        #register_method
        assert "identity" == ph.get_function_name()

    def test_reference(self):
        add_ref = ph.ref('add_ref')

        assert 8 == 3 >> ph.Compile(ph.add(2).on(add_ref).add(3))
        assert 5 == add_ref()

    def test_ref_props(self):

        a = ph.ref('a')
        b = ph.ref('b')

        assert [7, 3, 5] == ph.Pipe(
            1,
            add2, a.set,
            add2, b.set,
            add2,
            [
                (),
                a,
                b
            ]
        )

    def test_scope_property(self):

        assert "some random text" == ph.Pipe(
            "some ",
            ph.With( DummyContext("random "),
            (
                lambda s: s + ph.Scope(),
                ph.With( DummyContext("text"),
                    lambda s: s + ph.Scope()
                )
            )
            )
        )

        assert ph.Scope() == None

    def test_ref_integraton_with_dsl(self):

        y = ph.ref('y')


        assert 5 == ph.Pipe(
            1,
            _ + 4,
            ph.on(y),
            _ * 10,
            'y'
        )

        assert 5 == ph.Pipe(
            1,
            _ + 4,
            ph.on(y),
            _ * 10,
            'y'
        )

        assert 5 == ph.Pipe(
            1,
            _ + 4,
            ph.on('y'),
            _ * 10,
            'y'
        )

    def test_list(self):

        assert [['4', '6'], [4, 6]] == ph.Pipe(
            3,
            [
                _ + 1
            ,
                _ * 2
            ],
            [
                ph._2(map, str)
            ,
                ()
            ]
        )
