# coding=utf8
# -*- coding: utf8 -*-
#
#      LaTeX Expression : Python module for easy LaTeX typesetting of algebraic
#  expressions in symbolic form with automatic substitution and result computation
#
#                       Copyright (C)  2013-2015  Jan Stransky
#                       Copyright (C)  2022  	  Jakub Kaderka
#                       Copyright (C)  2024  	  Andrew Young
#
#  LaTeX Expression is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by the
#  Free Software Foundation, either version 3 of the License, or (at your option)
#  any later version.
#
#  LaTeX Expression is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
#  details.
#
#  You should have received a copy of the GNU Lesser General Public License along
#  with this program. If not, see <http://www.gnu.org/licenses/>.

r"""latexexpr_efficalc.sympy is an extension for LaTeXExpression for symbolic operations (specifically :func:`.simplify`, :func:`.expand`, :func:`factor`, :func:`collect`, :func:`cancel`, :func:`apart` functions). It requires `sympy <http://www.sympy.org>`_ module. Most of the examples in this documentation is borrowed from `sympy documentation <http://docs.sympy.org/dev/tutorial/simplification.html>`_.

Note the sympy module has not yet been fully implemented and tested. If you would like to improve the library, please reach out or raise a PR with your proposed improvements.

If `sympy <http://www.sympy.org>`_ is present, it also defines aforementioned methods on :class:`Expression <latexexpr_efficalc.Expression>` and :class:`Operation <latexexpr_efficalc.Operation>` classes, so it is possible to use both :func:`.simplify` and o.simplify():

.. code-block:: python

	>>> import latexexpr_efficalc.sympy as lsympy
	>>> v1 = latexexpr_efficalc.Variable('v1',None)
	>>> v2 = latexexpr_efficalc.Variable('v2',None)
	>>> v3 = latexexpr_efficalc.Variable('v3',1.23)
	>>> v4 = latexexpr_efficalc.Variable('v4',4.56)
	>>> x = latexexpr_efficalc.Variable('x',None)
	>>> e1 = latexexpr_efficalc.Expression('e1',v1+v1+v2+v3+v2+v3-v4)
	>>> print e1
	e1 = {v1} + {v1} + {v2} + {v3} + {v2} + {v3} - {v4}
	>>> print lsympy.simplify(e1)
	e1 = \left( - {v4} \right) + {2} \cdot {v1} + {2} \cdot {v2} + {2} \cdot {v3}
	>>> print lsympy.simplify(e1,substituteFloats=True)
	e1 = {-2.1} + {2} \cdot {v1} + {2} \cdot {v2}
	>>> e1.simplify()
	>>> print e1
	e1 = \left( - {v4} \right) + {2} \cdot {v1} + {2} \cdot {v2} + {2} \cdot {v3}
	>>> e1.simplify(substituteFloats=True)
	>>> print e1
	e1 = {-2.1} + {2} \cdot {v1} + {2} \cdot {v2}
	>>> e2 = latexexpr_efficalc.Expression('e2',latexexpr_efficalc.sin(x)**2+latexexpr_efficalc.cos(x)**2)
	>>> print lsympy.simplify(e2)
	e2 = 1 = 1 \ \mathrm{} = 1 \ \mathrm{}
	>>> e3 = latexexpr_efficalc.Expression('e3', (x**3 + x**2 - x - 1) / (x**2 + 2*x + 1) )
	>>> print lsympy.simplify(e3)
	e3 = {-1} + {x}
"""

import copy
import latexexpr_efficalc

try:
    import sympy
except ImportError:
    raise ImportError(
        "module 'sympy' is not available, therefore latexexpr_efficalc.sympy will not be available"
    )


def _operation_to_sympy(arg, varMap=None, substituteFloats=True):
    sf = substituteFloats
    if varMap is None:
        varMap = {}
    if isinstance(arg, latexexpr_efficalc.Variable):
        if not arg.is_symbolic() and arg.name == "%g" % arg.value:
            if arg.value == int(arg.value):
                return int(arg), varMap
            return float(arg), varMap
        if not sf or arg.is_symbolic():
            varMap[arg.name] = arg
            return sympy.Symbol(arg.name), varMap
        return float(arg), varMap
    if isinstance(arg, latexexpr_efficalc.Expression):
        return _operation_to_sympy(arg.operation, varMap, sf)
    if not isinstance(arg, latexexpr_efficalc.Operation):
        raise TypeError("TODO " + str(type(arg)) + str(arg))
    t = arg.type
    if t in latexexpr_efficalc._supportedOperationsN:
        if t == latexexpr_efficalc._ADD:
            sympyOp = sympy.Add
        elif t == latexexpr_efficalc._MUL:
            sympyOp = sympy.Mul
        # elif t == latexexpr_efficalc._MAX: sympyOp = sympy.add.Add # TODO
        # elif t == latexexpr_efficalc._MIN: sympyOp = sympy.add.Add # TODO
        args = [_o2s(a, varMap, sf) for a in arg.args]
        return sympyOp(*args), varMap
    if t in latexexpr_efficalc._supportedOperations2:
        a = arg.args
        if t == latexexpr_efficalc._SUB:
            sympyOp, args = sympy.Add, (
                _o2s(a[0], varMap, sf),
                sympy.Mul(-1, _o2s(a[1], varMap, sf)),
            )
        elif t == latexexpr_efficalc._DIV or t == latexexpr_efficalc._DIV2:
            sympyOp, args = sympy.Mul, (
                _o2s(a[0], varMap, sf),
                sympy.power.Pow(_o2s(a[1], varMap, sf), -1),
            )
        elif t == latexexpr_efficalc._POW:
            sympyOp, args = sympy.Pow, (_o2s(a[0], varMap, sf), _o2s(a[1], varMap, sf))
        elif t == latexexpr_efficalc._ROOT:
            sympyOp, args = sympy.Pow, (_o2s(a[0], varMap, sf), _o2s(-a[1], varMap, sf))
        elif t == latexexpr_efficalc._LOG:
            sympyOp, args = sympy.log, (_o2s(a[0], varMap, sf), _o2s(a[1], varMap, sf))
        return sympyOp(*args), varMap
    if t in latexexpr_efficalc._supportedOperations1:
        a = arg.args[0]
        if t == latexexpr_efficalc._NEG:
            sympyOp, args = sympy.Mul, (_o2s(a, varMap, sf), -1)
        elif t == latexexpr_efficalc._ABS:
            sympyOp, args = sympy.Abs, None
        elif t == latexexpr_efficalc._SQR:
            sympyOp, args = sympy.Pow, (_o2s(a, varMap, sf), 2)
        elif t == latexexpr_efficalc._SQRT:
            sympyOp, args = sympy.Pow, (_o2s(a, varMap, sf), -2)
        elif t == latexexpr_efficalc._SIN:
            sympyOp, args = sympy.sin, None
        elif t == latexexpr_efficalc._COS:
            sympyOp, args = sympy.cos, None
        elif t == latexexpr_efficalc._TAN:
            sympyOp, args = sympy.tan, None
        elif t == latexexpr_efficalc._SINH:
            sympyOp, args = sympy.sinh, None
        elif t == latexexpr_efficalc._COSH:
            sympyOp, args = sympy.sinh, None
        elif t == latexexpr_efficalc._TANH:
            sympyOp, args = sympy.sinh, None
        elif t == latexexpr_efficalc._EXP:
            sympyOp, args = sympy.exp, None
        elif t == latexexpr_efficalc._LN:
            sympyOp, args = sympy.log, None
        elif t == latexexpr_efficalc._LOG10:
            sympyOp, args = sympy.log, (a, 10)  # TODO check formula
        elif t in (
            latexexpr_efficalc._NONE,
            latexexpr_efficalc._RBRACKETS,
            latexexpr_efficalc._SBRACKETS,
            latexexpr_efficalc._CBRACKETS,
            latexexpr_efficalc._ABRACKETS,
            latexexpr_efficalc._POS,
        ):
            return _operation_to_sympy(a, varMap, sf)
        if args is None:
            args = (_o2s(a, varMap, sf),)
        return sympyOp(*args), varMap
    raise latexexpr_efficalc.LaTeXExpressionError("TODO")


def _o2s(arg, varMap, substituteFloats):
    return _operation_to_sympy(arg, varMap, substituteFloats)[0]


def _sympy2operation(sympyExpr, varMap):
    if sympyExpr.is_Float or sympyExpr.is_Integer:
        if isinstance(sympyExpr, sympy.numbers.Exp1):
            name = "e"
        elif isinstance(sympyExpr, sympy.numbers.Pi):
            name = r"\pi"
        # TODO?
        else:
            name = "%g" % float(sympyExpr)
        return latexexpr_efficalc.Variable(name, float(sympyExpr))
    #
    if isinstance(sympyExpr, sympy.Symbol):
        return varMap[sympyExpr.name]
    args = [_s2o(a, varMap) for a in sympyExpr.args]
    if isinstance(sympyExpr, sympy.Add):
        if (
            len(args) == 2
            and isinstance(args[1], latexexpr_efficalc.Operation)
            and args[1].type == latexexpr_efficalc._NEG
        ):
            args[1] = args[1].args[0]
            return latexexpr_efficalc.sub(*args)
        return latexexpr_efficalc.add(*args)
    if isinstance(sympyExpr, sympy.Mul):
        if len(args) == 2:
            if (
                isinstance(args[0], latexexpr_efficalc.Variable)
                and args[0].name == "-1"
            ):
                return -args[1]
            if (
                isinstance(args[1], latexexpr_efficalc.Variable)
                and args[1].name == "-1"
            ):
                return -args[0]
        elif (
            len(args) == 2
            and isinstance(args[1], latexexpr_efficalc.Operation)
            and args[1].type == latexexpr_efficalc._DIV
        ):
            if args[1].args[0].value == 1.0:
                return args[0] / args[1].args[1]
            if all(
                a.type == latexexpr_efficalc._LN for a in (args[0], args[1].args[0])
            ):
                return latexexpr_efficalc._LOG(args[0], args[0].args[1])
        for i, a in enumerate(args):
            t = (
                a.type
                if isinstance(a, latexexpr_efficalc.Operation)
                else (
                    a.operation.type
                    if isinstance(a, latexexpr_efficalc.Expression)
                    else None
                )
            )
            if t in (latexexpr_efficalc._ADD, latexexpr_efficalc._SUB):  # TODO?
                args[i] = latexexpr_efficalc.brackets(a)
        return latexexpr_efficalc.mul(*args)
    if isinstance(sympyExpr, sympy.Pow):
        if len(args) == 2:
            n = (
                args[1].name
                if isinstance(args[1], latexexpr_efficalc.Variable)
                else None
            )
            if n == "-1":
                return 1.0 / args[0]
            if n == "2":
                return args[0] ** 2
            if n == "0.5":
                return latexexpr_efficalc._SQRT(args[1])
        # TODO arg ^ int?
        a = args[0]
        t = (
            a.type
            if isinstance(a, latexexpr_efficalc.Operation)
            else (
                a.operation.type
                if isinstance(a, latexexpr_efficalc.Expression)
                else None
            )
        )
        if t in (latexexpr_efficalc._ADD, latexexpr_efficalc._SUB):  # TODO?
            args[0] = latexexpr_efficalc.brackets(a)
        return args[0] ** args[1]
    for s, l in (
        (sympy.Abs, latexexpr_efficalc.absolute),
        (sympy.sin, latexexpr_efficalc.sin),
        (sympy.cos, latexexpr_efficalc.cos),
        (sympy.tan, latexexpr_efficalc.tan),
        (sympy.sinh, latexexpr_efficalc.sinh),
        (sympy.cosh, latexexpr_efficalc.cosh),
        (sympy.tanh, latexexpr_efficalc.tanh),
        (sympy.tanh, latexexpr_efficalc.tanh),
        (sympy.log, latexexpr_efficalc.ln),
    ):
        if isinstance(sympyExpr, s):
            return l(args[0])
    if isinstance(sympyExpr, sympy.Rational):
        p, q = sympyExpr.p, sympyExpr.q
        if p > 0:
            return latexexpr_efficalc.Variable(str(p), p) / latexexpr_efficalc.Variable(
                str(q), q
            )
        p = -p
        return -(
            latexexpr_efficalc.Variable(str(p), p)
            / latexexpr_efficalc.Variable(str(q), q)
        )
    #
    # TODO
    raise latexexpr_efficalc.LaTeXExpressionError("TODO")


_s2o = _sympy2operation


def simplify(arg, substituteFloats=False, **kw):
    r"""Performs simplify operation on arg. Symbolic variables are left symbolic, but variables with values are treated as the values (!)

    :param Variable|Operation|Expression arg: argument to be processed
    :param bool substituteFloats: non-symbolic variables are treated as their float values if True, they are left otherwise
    :param \*\*kw: keywords for sympy.simplify() function
    :rtype: type(arg)

    .. code-block:: python

            >>> import latexexpr_efficalc.sympy as lsympy
            >>> v1 = latexexpr_efficalc.Variable('v1',None)
            >>> v2 = latexexpr_efficalc.Variable('v2',None)
            >>> v3 = latexexpr_efficalc.Variable('v3',1.23)
            >>> v4 = latexexpr_efficalc.Variable('v4',4.56)
            >>> x = latexexpr_efficalc.Variable('x',None)
            >>> e1 = latexexpr_efficalc.Expression('e1',v1+v1+v2+v3+v2+v3-v4)
            >>> print e1
            e1 = {v1} + {v1} + {v2} + {v3} + {v2} + {v3} - {v4}
            >>> print lsympy.simplify(e1)
            e1 = \left( - {v4} \right) + {2} \cdot {v1} + {2} \cdot {v2} + {2} \cdot {v3}
            >>> print lsympy.simplify(e1,substituteFloats=True)
            e1 = {-2.1} + {2} \cdot {v1} + {2} \cdot {v2}
            >>> e1.simplify()
            >>> print e1
            e1 = \left( - {v4} \right) + {2} \cdot {v1} + {2} \cdot {v2} + {2} \cdot {v3}
            >>> e1.simplify(substituteFloats=True)
            >>> print e1
            e1 = {-2.1} + {2} \cdot {v1} + {2} \cdot {v2}
            >>> e2 = latexexpr_efficalc.Expression('e2',latexexpr_efficalc.sin(x)**2+latexexpr_efficalc.cos(x)**2)
            >>> print lsympy.simplify(e2)
            e2 = 1 = 1 \ \mathrm{} = 1 \ \mathrm{}
            >>> e3 = latexexpr_efficalc.Expression('e3', (x**3 + x**2 - x - 1) / (x**2 + 2*x + 1) )
            >>> print lsympy.simplify(e3)
            e3 = {-1} + {x}
    """
    if isinstance(arg, latexexpr_efficalc.Variable):
        return arg
    if isinstance(arg, latexexpr_efficalc.Expression):
        ret = copy.copy(arg)
        ret.simplify(substituteFloats, **kw)
        return ret
    if isinstance(arg, latexexpr_efficalc.Operation):
        s, lVars = _operation_to_sympy(arg, substituteFloats=substituteFloats)
        s = sympy.simplify(s, **kw)
        return _sympy2operation(s, lVars)
    raise TypeError("Unsupported type (%s) for simplify" % (arg.__class__.__name__))


latexexpr_efficalc.Expression.simplify = (
    lambda self, substituteFloats=False, **kw: _setOperation(
        self, simplify(self.operation, substituteFloats=substituteFloats, **kw)
    )
)

latexexpr_efficalc.Operation.simplify = (
    lambda self, substituteFloats=False, **kw: _copyOperation(
        self, simplify(self, substituteFloats=substituteFloats, **kw)
    )
)


def expand(arg, substituteFloats=False, **kw):
    r"""Performs expand operation on arg. Symbolic variables are left symbolic, but variables with values are treated as the values (!)

    :param Variable|Operation|Expression arg: argument to be processed
    :param bool substituteFloats: non-symbolic variables are treated as their float values if True, they are left otherwise
    :param \*\*kw: keywords for sympy.expand() function
    :rtype: type(arg)

    .. code-block:: python

            >>> import latexexpr_efficalc.sympy as lsympy
            >>> x = latexexpr_efficalc.Variable('x',None)
            >>> e1 = latexexpr_efficalc.Expression('e1', (x+1)**2 )
            >>> print lsympy.expand(e1,substituteFloats=True)
            e1 = {1} + {2} \cdot {x} + { {x} }^{ {2} }
            >>> e2 = latexexpr_efficalc.Expression('e2', (x+2)*(x-3) )
            >>> print lsympy.expand(e2)
            e2 = {-6} + \left( - {x} \right) + { {x} }^{ {2} }
            >>> e3 = latexexpr_efficalc.Expression('e3', (x+1)*(x-2) - (x-1)*x )
            >>> print lsympy.expand(e3)
            e3 = -2 = \left( -2 \right) \ \mathrm{} = \left(-2\right) \ \mathrm{}
    """
    if isinstance(arg, latexexpr_efficalc.Variable):
        return arg
    if isinstance(arg, latexexpr_efficalc.Expression):
        ret = copy.copy(arg)
        ret.expand(substituteFloats, **kw)
        return ret
    if isinstance(arg, latexexpr_efficalc.Operation):
        s, lVars = _operation_to_sympy(arg, substituteFloats=substituteFloats)
        s = sympy.expand(s, **kw)
        return _sympy2operation(s, lVars)
    raise TypeError("Unsupported type (%s) for expand" % (arg.__class__.__name__))


latexexpr_efficalc.Expression.expand = (
    lambda self, substituteFloats=False, **kw: _setOperation(
        self, expand(self.operation, substituteFloats=substituteFloats, **kw)
    )
)

latexexpr_efficalc.Operation.expand = (
    lambda self, substituteFloats=False, **kw: _copyOperation(
        self, expand(self, substituteFloats=substituteFloats, **kw)
    )
)


def factor(arg, substituteFloats=False, **kw):
    r"""Performs factor operation on arg. Symbolic variables are left symbolic, but variables with values are treated as the values (!)

    :param Variable|Operation|Expression arg: argument to be processed
    :param bool substituteFloats: non-symbolic variables are treated as their float values if True, they are left otherwise
    :param \*\*kw: keywords for sympy.factor() function
    :rtype: type(arg)

    .. code-block:: python

            >>> import latexexpr_efficalc.sympy as lsympy
            >>> x = latexexpr_efficalc.Variable('x',None)
            >>> y = latexexpr_efficalc.Variable('y',None)
            >>> z = latexexpr_efficalc.Variable('z',None)
            >>> e1 = latexexpr_efficalc.Expression('e1', x**3 - x**2 + x - 1)
            >>> print lsympy.factor(e1)
            e1 = \left( {1} + { {x} }^{ {2} } \right) \cdot \left( {-1} + {x} \right)
            >>> e2 = latexexpr_efficalc.Expression('e2', x**2*z + 4*x*y*z + 4*y**2*z)
            >>> print lsympy.factor(e2)
            e2 = {z} \cdot { {2} \cdot {y} + {x} }^{ {2} }
    """
    if isinstance(arg, latexexpr_efficalc.Variable):
        return arg
    if isinstance(arg, latexexpr_efficalc.Expression):
        ret = copy.copy(arg)
        ret.factor(substituteFloats, **kw)
        return ret
    if isinstance(arg, latexexpr_efficalc.Operation):
        s, lVars = _operation_to_sympy(arg, substituteFloats=substituteFloats)
        s = sympy.factor(s, **kw)
        return _sympy2operation(s, lVars)
    raise TypeError("Unsupported type (%s) for factor" % (arg.__class__.__name__))


latexexpr_efficalc.Expression.factor = (
    lambda self, substituteFloats=False, **kw: _setOperation(
        self, factor(self.operation, substituteFloats=substituteFloats, **kw)
    )
)

latexexpr_efficalc.Operation.factor = (
    lambda self, substituteFloats=False, **kw: _copyOperation(
        self, factor(self, substituteFloats=substituteFloats, **kw)
    )
)


def collect(arg, syms, substituteFloats=False, **kw):
    r"""Performs collect operation on arg. Symbolic variables are left symbolic, but variables with values are treated as the values (!)

    :param Variable|Operation|Expression arg: argument to be processed
    :param Variable|[Variable] syms: variables to be collected
    :param bool substituteFloats: non-symbolic variables are treated as their float values if True, they are left otherwise
    :param \*\*kw: keywords for sympy.collect() function
    :rtype: type(arg)

    .. code-block:: python

            >>> import latexexpr_efficalc.sympy as lsympy
            >>> x = latexexpr_efficalc.Variable('x',None)
            >>> y = latexexpr_efficalc.Variable('y',None)
            >>> z = latexexpr_efficalc.Variable('z',None)
            >>> e1 = latexexpr_efficalc.Expression('e1', x*y + x - 3  + 2*x**2 - z*x**2 + x**3)
            >>> print lsympy.collect(e1,x)
            e1 = {-3} + { {x} }^{ {3} } + {x} \cdot \left( {1} + {y} \right) + { {x} }^{ {2} } \cdot \left( {2} - {z} \right)
    """
    if isinstance(arg, latexexpr_efficalc.Variable):
        return arg
    if isinstance(arg, latexexpr_efficalc.Expression):
        ret = copy.copy(arg)
        ret.collect(syms, substituteFloats, **kw)
        return ret
    if isinstance(arg, latexexpr_efficalc.Operation):
        s, lVars = _operation_to_sympy(arg, substituteFloats=substituteFloats)
        if not (
            isinstance(syms, latexexpr_efficalc.Variable)
            or all(isinstance(latexexpr_efficalc.Variable(s) for s in syms))
        ):
            raise latexexpr_efficalc.LaTeXExpressionError("TODO")
        syms = (
            sympy.Symbol(syms.name)
            if isinstance(syms, latexexpr_efficalc.Variable)
            else [sympy.Symbol(s.name) for s in syms]
        )
        s = sympy.collect(s, syms, **kw)
        return _sympy2operation(s, lVars)
    raise TypeError("Unsupported type (%s) for collect" % (arg.__class__.__name__))


latexexpr_efficalc.Expression.collect = (
    lambda self, syms, substituteFloats=False, **kw: _setOperation(
        self, collect(self.operation, syms, substituteFloats=substituteFloats, **kw)
    )
)

latexexpr_efficalc.Operation.collect = (
    lambda self, syms, substituteFloats=False, **kw: _copyOperation(
        self, collect(self, syms, substituteFloats=substituteFloats, **kw)
    )
)


def cancel(arg, substituteFloats=False, **kw):
    r"""Performs cancel operation on arg. Symbolic variables are left symbolic, but variables with values are treated as the values (!)

    :param Variable|Operation|Expression arg: argument to be processed
    :param bool substituteFloats: non-symbolic variables are treated as their float values if True, they are left otherwise
    :param \*\*kw: keywords for sympy.cancel() function
    :rtype: type(arg)

    .. code-block:: python

            >>> import latexexpr_efficalc.sympy as lsympy
            >>> x = latexexpr_efficalc.Variable('x',None)
            >>> y = latexexpr_efficalc.Variable('y',None)
            >>> z = latexexpr_efficalc.Variable('z',None)
            >>> e1 = latexexpr_efficalc.Expression('e1', (x**2 + 2*x + 1) / (x**2 + x) )
            >>> print lsympy.cancel(e1)
            e1 = \frac{ {1} }{ {x} } \cdot \left( {1} + {x} \right)
            >>> e2 = latexexpr_efficalc.Expression('e2', 1/x + (3*x/2 - 2) / (x - 4) )
            >>> print lsympy.cancel(e2)
            e2 = \frac{ {1} }{ {2} \cdot { {x} }^{ {2} } + {-8} \cdot {x} } \cdot \left( {-8} + {-2} \cdot {x} + {3} \cdot { {x} }^{ {2} } \right)
            >>> e3 = latexexpr_efficalc.Expression('e3', (x*y**2 - 2*x*y*z + x*z**2 + y**2 - 2*y*z + z**2) / (x**2 - 1) )
            >>> print lsympy.cancel(e3)
            e3 = \frac{ {1} }{ {-1} + {x} } \cdot \left( { {z} }^{ {2} } + {-2} \cdot {y} \cdot {z} + { {y} }^{ {2} } \right)
    """
    if isinstance(arg, latexexpr_efficalc.Variable):
        return arg
    if isinstance(arg, latexexpr_efficalc.Expression):
        ret = copy.copy(arg)
        ret.cancel(substituteFloats, **kw)
        return ret
    if isinstance(arg, latexexpr_efficalc.Operation):
        s, lVars = _operation_to_sympy(arg, substituteFloats=substituteFloats)
        s = sympy.cancel(s, **kw)
        return _sympy2operation(s, lVars)
    raise TypeError("Unsupported type (%s) for cancel" % (arg.__class__.__name__))


latexexpr_efficalc.Expression.cancel = (
    lambda self, substituteFloats=False, **kw: _setOperation(
        self, cancel(self.operation, substituteFloats=substituteFloats, **kw)
    )
)

latexexpr_efficalc.Operation.cancel = (
    lambda self, substituteFloats=False, **kw: _copyOperation(
        self, cancel(self, substituteFloats=substituteFloats, **kw)
    )
)


def apart(arg, substituteFloats=False, **kw):
    r"""Performs apart operation on arg. Symbolic variables are left symbolic, but variables with values are treated as the values (!)

    :param Variable|Operation|Expression arg: argument to be processed
    :param bool substituteFloats: non-symbolic variables are treated as their float values if True, they are left otherwise
    :param \*\*kw: keywords for sympy.apart() function
    :rtype: type(arg)

    .. code-block:: python

            >>> import latexexpr_efficalc.sympy as lsympy
            >>> x = latexexpr_efficalc.Variable('x',None)
            >>> e1 = latexexpr_efficalc.Expression('e1', (4*x**3 + 21*x**2 + 10*x + 12) / (x**4 + 5*x**3 + 5*x**2 + 4*x) )
            >>> print lsympy.apart(e1)
            e1 = \frac{ {1} }{ {1} + {x} + { {x} }^{ {2} } } \cdot \left( {-1} + {2} \cdot {x} \right) + \left( - \frac{ {1} }{ {4} + {x} } \right) + {3} \cdot \frac{ {1} }{ {x} }
    """
    if isinstance(arg, latexexpr_efficalc.Variable):
        return arg
    if isinstance(arg, latexexpr_efficalc.Expression):
        ret = copy.copy(arg)
        ret.apart(substituteFloats, **kw)
        return ret
    if isinstance(arg, latexexpr_efficalc.Operation):
        s, lVars = _operation_to_sympy(arg, substituteFloats=substituteFloats)
        s = sympy.apart(s, **kw)
        return _sympy2operation(s, lVars)
    raise TypeError("Unsupported type (%s) for apart" % (arg.__class__.__name__))


latexexpr_efficalc.Expression.apart = (
    lambda self, substituteFloats=False, **kw: _setOperation(
        self, apart(self.operation, substituteFloats=substituteFloats, **kw)
    )
)

latexexpr_efficalc.Operation.apart = (
    lambda self, substituteFloats=False, **kw: _copyOperation(
        self, apart(self, substituteFloats=substituteFloats, **kw)
    )
)


# TODO other simplify-like functions?


def _setOperation(expr, operation):
    expr.operation = operation


def _copyOperation(o1, o2):
    o1.type = o2.type
    o1.args = o2.args
    o1.format = o2.format
    o1.exponent = o2.exponent


# TESTING
if __name__ == "__main__":
    import latexexpr_efficalc.sympy as lsympy

    v1 = latexexpr_efficalc.Variable("v1", None)
    v2 = latexexpr_efficalc.Variable("v2", None)
    v3 = latexexpr_efficalc.Variable("v3", 1.23)
    v4 = latexexpr_efficalc.Variable("v4", 4.56)
    x = latexexpr_efficalc.Variable("x", None)
    e1 = latexexpr_efficalc.Expression("e1", v1 + v1 + v2 + v3 + v2 + v3 - v4)
    print(e1)
    print(lsympy.simplify(e1))
    print(lsympy.simplify(e1, substituteFloats=True))
    e1.simplify()
    print(e1)
    e1.simplify(substituteFloats=True)
    print(e1)
    e2 = latexexpr_efficalc.Expression(
        "e2", latexexpr_efficalc.sin(x) ** 2 + latexexpr_efficalc.cos(x) ** 2
    )
    print(lsympy.simplify(e2))
    e3 = latexexpr_efficalc.Expression("e3", (x**3 + x**2 - x - 1) / (x**2 + 2 * x + 1))
    print(lsympy.simplify(e3))

    import latexexpr_efficalc.sympy as lsympy

    v1 = latexexpr_efficalc.Variable("v1", None)
    v2 = latexexpr_efficalc.Variable("v2", None)
    v3 = latexexpr_efficalc.Variable("v3", 1.23)
    v4 = latexexpr_efficalc.Variable("v4", 4.56)
    x = latexexpr_efficalc.Variable("x", None)
    e1 = latexexpr_efficalc.Expression("e1", v1 + v1 + v2 + v3 + v2 + v3 - v4)
    print(e1)
    print(lsympy.simplify(e1))
    print(lsympy.simplify(e1, substituteFloats=True))
    e1.simplify()
    print(e1)
    e1.simplify(substituteFloats=True)
    print(e1)
    e2 = latexexpr_efficalc.Expression(
        "e2", latexexpr_efficalc.sin(x) ** 2 + latexexpr_efficalc.cos(x) ** 2
    )
    print(lsympy.simplify(e2))
    e3 = latexexpr_efficalc.Expression("e3", (x**3 + x**2 - x - 1) / (x**2 + 2 * x + 1))
    print(lsympy.simplify(e3))

    import latexexpr_efficalc.sympy as lsympy

    x = latexexpr_efficalc.Variable("x", None)
    e1 = latexexpr_efficalc.Expression("e1", (x + 1) ** 2)
    print(lsympy.expand(e1, substituteFloats=True))
    e2 = latexexpr_efficalc.Expression("e2", (x + 2) * (x - 3))
    print(lsympy.expand(e2))
    e3 = latexexpr_efficalc.Expression("e3", (x + 1) * (x - 2) - (x - 1) * x)
    print(lsympy.expand(e3))

    import latexexpr_efficalc.sympy as lsympy

    x = latexexpr_efficalc.Variable("x", None)
    y = latexexpr_efficalc.Variable("y", None)
    z = latexexpr_efficalc.Variable("z", None)
    e1 = latexexpr_efficalc.Expression("e1", x**3 - x**2 + x - 1)
    print(lsympy.factor(e1))
    e2 = latexexpr_efficalc.Expression("e2", x**2 * z + 4 * x * y * z + 4 * y**2 * z)
    print(lsympy.factor(e2))

    import latexexpr_efficalc.sympy as lsympy

    x = latexexpr_efficalc.Variable("x", None)
    y = latexexpr_efficalc.Variable("y", None)
    z = latexexpr_efficalc.Variable("z", None)
    e1 = latexexpr_efficalc.Expression("e1", x * y + x - 3 + 2 * x**2 - z * x**2 + x**3)
    print(lsympy.collect(e1, x))

    import latexexpr_efficalc.sympy as lsympy

    x = latexexpr_efficalc.Variable("x", None)
    y = latexexpr_efficalc.Variable("y", None)
    z = latexexpr_efficalc.Variable("z", None)
    e1 = latexexpr_efficalc.Expression("e1", (x**2 + 2 * x + 1) / (x**2 + x))
    print(lsympy.cancel(e1))
    e2 = latexexpr_efficalc.Expression("e2", 1 / x + (3 * x / 2 - 2) / (x - 4))
    print(lsympy.cancel(e2))
    e3 = latexexpr_efficalc.Expression(
        "e3",
        (x * y**2 - 2 * x * y * z + x * z**2 + y**2 - 2 * y * z + z**2) / (x**2 - 1),
    )
    print(lsympy.cancel(e3))

    import latexexpr_efficalc.sympy as lsympy

    x = latexexpr_efficalc.Variable("x", None)
    e1 = latexexpr_efficalc.Expression(
        "e1",
        (4 * x**3 + 21 * x**2 + 10 * x + 12) / (x**4 + 5 * x**3 + 5 * x**2 + 4 * x),
    )
    print(lsympy.apart(e1))
######################################################################
