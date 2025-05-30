from sympy.logic.boolalg import BooleanFunction
from order_of_magnitude import *
from sympy.core.expr import Expr
from fractions import Fraction

# Support for some expressions that come up in the Littlewood-Paley theory arising in PDE

def sqrt(x):
    return x**Fraction(1,2)

def bracket(x):
    """
    The "Japanese bracket" notation.
    """
    return sqrt(1 + abs(x)**2)


class LittlewoodPaley(BooleanFunction):
    """
    The relation between n orders of magnitude X_1, ..., X_n that asserts that the largest one is the sum of all the others.  This scenario often arises when analyzing nonlinear frequency interactions.  Can be unpacked using `Cases`."""

    def __new__(cls, *args):
        if len(args) < 2:
            raise ValueError("LittlewoodPaley() requires at least two arguments.")
        if len(args) == 2:  # LP collapses to asymptotic equivalence when there are just two arguments
            return asymp(args[0], args[1])
        newargs = [Theta(x) for x in args]
        obj = Expr.__new__(cls, *newargs)
        obj.name = "LittlewoodPaley(" + ", ".join([str(arg) for arg in newargs]) + ")"
        return obj

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return str(self)   

    def _sympystr(self, printer):
        return str(self)
