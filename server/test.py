import flask
import sqlalchemy

flask.app

print("Hello, World!")

l = []
l.append(1)
c = l.count()
sqlalchemy.Float()


class C:
    """A test class.

    Does nothing,
    """

    def m(self):
        return C()


def n() -> C:
    return C()


o = C()
x = o.m()
n().m()

flask.flash('ffff')
flask.current_app


def f(x, y):
    return x + y


def g(x: int) -> int:
    return x
