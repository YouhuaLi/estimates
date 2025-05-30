from type import *
from fractions import Fraction

class Expression(Type):
    """A formal expression that represents an order of magnitude."""
    def add(self, other):
        """Automatically flatten sums."""
        summands = []
        if isinstance(self, Add):
            for summand in self.summands:
                summands.append(summand)
        else:
            summands.append(self)
        if isinstance(other, Add):
            for summand in other.summands:
                summands.append(summand)
        else:
            summands.append(other)
        return Add(*summands)
    def __add__(self, other):
        return self.add(ensure_expr(other))
    def __radd__(self, other):
        return ensure_expr(other).add(self)
    def mul(self, other):
        """Automatically flatten products."""
        factors = []
        if isinstance(self, Mul):
            for factor in self.factors:
                factors.append(factor)
        else:
            factors.append(self)
        if isinstance(other, Mul):
            for factor in other.factors:
                factors.append(factor)
        else:
            factors.append(other)
        return Mul(*factors)
    def __pow__(self, other):
        return Power(self, other)
    def __mul__(self, other):
        return self.mul(ensure_expr(other))
    def __rmul__(self, other):
        return ensure_expr(other).mul(self)
    def __truediv__(self, other):
        return Div(self, ensure_expr(other))
    def __rtruediv__(self, other):
        return Div(ensure_expr(other), self)



def ensure_expr(obj):
    """If obj is already an Expression, return it;
       otherwise wrap it in a Constant."""
    return obj if isinstance(obj, Expression) else Constant(obj)

class Variable(Expression):
    """A variable magnitude."""
    def __init__(self, name):
        self.name = name
        self.operands = []

class Constant(Expression):
    """A constant magnitude."""
    def __init__(self, value):
        assert isinstance(value, (int, float)), "Constant value must be an int or float."
        assert value > 0, "Constant value must be positive."
        self.value = value
        self.operands = []
    def defeq(self, other):
        """Check if two constants are definitionally equal (i.e., have the same value)."""
        if isinstance(other, Constant):
            return self.value == other.value
        return False
    def simp(self, hypotheses=()):
        """Because we are working with orders of magnitude, constants can be simplified to 1."""
        return Constant(1)
    def __str__(self):
        return str(self.value)

class Max(Expression):
    """The formal maximum of a set of expressions."""
    def __init__(self, *operands):
        assert len(operands) > 0, "Max must have at least one operand."
        self.operands = [ensure_expr(operand) for operand in operands]
    def defeq(self, other):
        if isinstance(other, Max):
            return set_defeq(self.operands, other.operands)
        return False
    def simp(self, hypotheses=()):
        """Simplify the max expression by flattening nested max's and removing duplicates."""
        new_operands = set()
        for op in self.operands:
            op = op.simp(hypotheses)
            if isinstance(op, Max):
                for sub_op in op.operands:
                    sub_op.add_to(new_operands)
            else:
                op.add_to(new_operands)
        assert len(new_operands) > 0, "Max must have at least one operand after simplification."
        if len(new_operands) == 1:
            return new_operands.pop()
        else:
            return Max(*new_operands)
    def __str__(self):
        inner = ", ".join(str(op) for op in self.operands)
        return f"max({inner})"

# Factory function (this will shadow Python's built‑in max in this module)
def max(*args):
    return Max(*args)

class Min(Expression):
    """The formal minimum of a set of expressions."""
    def __init__(self, *operands):
        assert len(operands) > 0, "Min must have at least one operand."
        self.operands = [ensure_expr(operand) for operand in operands]
    def defeq(self, other):
        if isinstance(other, Min):
            return set_defeq(self.operands, other.operands)
        return False
    def simp(self, hypotheses=()):
        """Simplify the min expression by flattening nested mins and removing duplicates."""
        new_operands = set()
        for op in self.operands:
            op = op.simp(hypotheses)
            if isinstance(op, Min):
                for sub_op in op.operands:
                    sub_op.add_to(new_operands)
            else:
                op.add_to(new_operands)
        assert len(new_operands) > 0, "Min must have at least one operand after simplification."
        if len(new_operands) == 1:
            return new_operands.pop()
        else:
            return Min(*new_operands)
    def __str__(self):
        inner = ", ".join(str(op) for op in self.operands)
        return f"min({inner})"
    
def min(*args):
    return Min(*args)

class Add(Expression):
    """The formal sum of a set of expressions."""
    def __init__(self, *summands):
        assert len(summands) > 0, "Add must have at least one summand."
        self.summands = [ensure_expr(summand) for summand in summands]
        self.operands = self.summands  
    def defeq(self, other):
        if isinstance(other, Add):
            return set_defeq(self.summands, other.summands)
        return False
    def simp(self, hypotheses=()):
        """For orders of magnitude, one can turn a sum into a max."""
        return Max(*self.summands).simp(hypotheses)
    def __str__(self):
        inner = " + ".join(str(sm) for sm in self.summands)
        return f"({inner})"

class Mul(Expression):
    """The formal product of a set of expressions."""
    def __init__(self, *factors):
        self.factors = [ensure_expr(factor) for factor in factors]
        self.operands = self.factors  
    def defeq(self, other):
        if isinstance(other, Mul):
            return set_defeq(self.factors, other.factors)
        return False
    def simp(self, hypotheses=()):
        """Simplify the product in several steps."""
        
        # First, flatten nested products and delete constants.
        new_factors = []
        for factor in self.factors:
            factor = factor.simp(hypotheses)
            if isinstance(factor, Mul):
                for sub_factor in factor.factors:
                    new_factors.append(sub_factor)
            elif isinstance(factor, Constant):
                continue  # multiplying by a constant has no effect in orders of magnitude
            else:
                new_factors.append(factor)

        # Next, gather terms (up to defeq) and combine exponents for powers.
        terms = {}
        for factor in new_factors:
            if isinstance(factor, Power):
                base = factor.base
                exponent = factor.exponent
            else:
                base = factor
                exponent = Fraction(1, 1)
            new = True
            for b in terms:
                if base.defeq(b):
                    terms[b] += exponent
                    new = False
                    break
            if new:
                terms[base] = exponent        

        # Simplify all monomials and remove constants
        final_factors = []
        for base, exponent in terms.items():
            monomial = Power(base,exponent).simp(hypotheses)
            if not isinstance(monomial,Constant):
                final_factors.append(monomial)

        return Mul(*final_factors)

    def __str__(self):
        inner = " * ".join(str(f) for f in self.factors)
        return f"({inner})"

class Div(Expression):
    """The formal quotient of two expressions."""
    def __init__(self, numerator, denominator):
        self.numerator = ensure_expr(numerator)
        self.denominator = ensure_expr(denominator)
        self.operands = [self.numerator, self.denominator]  
    def defeq(self, other):
        if isinstance(other, Div):
            return self.numerator.defeq(other.numerator) and self.denominator.defeq(other.denominator)
        return False
    def simp(self, hypotheses=()): 
        # appeal to Mul's simplifier to handle division
        return (self.numerator * (self.denominator**(-1))).simp(hypotheses)
    def __str__(self):
        return f"({self.numerator} / {self.denominator})"

class Power(Expression):
    """The formal power of an expression raised to an exponent.  To use exact arithmetic, exponents must be rational. """
    def __init__(self, base, exponent):
        self.base = ensure_expr(base)
        self.operands = [self.base]  # For compatibility with Max/Min
        if isinstance(exponent, int):
            self.exponent = Fraction(exponent, 1)  # Convert integer exponent to Fraction
        elif isinstance(exponent, Fraction):
            self.exponent = exponent
        else:
            raise ValueError(f"Exponent {exponent} must be an int or rational, was type {type(exponent)}.")
    def defeq(self, other):
        if isinstance(other, Power):
            return self.base.defeq(other.base) and self.exponent == other.exponent
        return False
    def simp(self, hypotheses=()):
        base = self.base.simp(hypotheses)
        if self.exponent == Fraction(1,1):
            return base  # x^1 simplifies to x
        if self.exponent == Fraction(0,1) or isinstance(base, Constant):
            return Constant(1)
        if isinstance(base, Power):
            # If the base is already a power, we can combine the exponents
            return Power(base.base, base.exponent * self.exponent)
        if isinstance(base, Mul):
            # distribute the exponent over the product
            return Mul(*(Power(factor, self.exponent) for factor in base.factors)).simp(hypotheses)
        return Power(base, self.exponent)
    def __str__(self):
        return f"({self.base} ^ {self.exponent})"

def sqrt(expr):
    return Power(expr, Fraction(1, 2))
Expression.sqrt = sqrt  # Add a convenience method to Expression

def bracket(expr):
    """ The "Japanese bracket" <x> = (1 + |x|^2)^{1/2} """
    return sqrt(Add(Constant(1), Power(expr, 2)))
Expression.bracket = bracket  # Add a convenience method to Expression

