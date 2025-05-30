from statements import *
from expressions import *
import itertools


# An estimate is a comparison between two expressions that is of one of the following forms:

## X <~ Y:  X = O(Y)
## X << Y:  X = o(Y)
## X ~ Y:   X << Y << X
## X >~ Y:  Y = O(X)
## X >> Y:  Y = o(X)

class Estimate(Statement):
    def __init__(self, left, operator, right):
        self.left = ensure_expr(left)
        self.right = ensure_expr(right)
        assert operator in ("<~", "<<", "~", ">~", ">>"), f"Invalid operator {operator} for Estimate."
        self.operator = operator 
        self.name = f"{self.left} {self.operator} {self.right}"
        
    def defeq(self, other):
        if isinstance(other, Estimate):
            return (self.left.defeq(other.left) and
                    self.right.defeq(other.right) and
                    self.operator == other.operator)
        return False

    def negate(self):
        match self.operator:
            case "<~":
                return Estimate(self.left,  ">>", self.right)
            case "<<":
                return Estimate(self.left, ">~", self.right)
            case "~":
                return Or( Estimate(self.left, ">>", self.right), Estimate(self.left, "<<", self.right) )
            case ">~":
                return Estimate(self.left, "<<", self.right)
            case ">>":
                return Estimate(self.left, "<~", self.right)
            case _:
                raise ValueError(f"Unknown operator {self.operator} in negate() method of Estimate.")
            
    def simp(self, hypotheses=set()):
        # Reverse \leq type inequalities to \geq to reach simp normal form
        if self.operator == "<~":  
            return Estimate(self.right, ">~", self.left).simp(hypotheses)
        if self.operator == "<<":  
            return Estimate(self.right, ">>", self.left).simp(hypotheses)

        # normalize RHS to 1 to reach simp normal form
        left = (self.left/self.right).simp(hypotheses)
        right = Constant(1)
    
        if left.defeq(right):
            return Bool(self.operator in ("<~", ">~", "~"))
    
        return Estimate(left, self.operator, right)
    

def expression_le(self, other):
    return Estimate(self, '<~', ensure_expr(other))
Expression.__le__ = expression_le
Expression.lesssim = expression_le  # alias for <~

def expression_lt(self, other):
    return Estimate(self, '<<', ensure_expr(other))
Expression.__lt__ = expression_lt
Expression.ll = expression_lt  # alias for <<

def expression_ge(self, other):
    return Estimate(self, '>~', ensure_expr(other))
Expression.__ge__ = expression_ge
Expression.gtrsim = expression_ge  # alias for >~

def expression_gt(self, other):
    return Estimate(self, '>>', ensure_expr(other))
Expression.__gt__ = expression_gt
Expression.gg = expression_gt  # alias for >>

def expression_eq(self, other):
    return Estimate(self, '~', ensure_expr(other))
Expression.asymp = expression_eq  # cannot override __eq__ because it is used for object identity, not equality of expressions
    
# the Littlewood-Paley property asserts that some collection N_1,...,N_k of variables are magnitudes (up to constants) of vectors that sum to zero.  Equivalently, two of them are comparable in magnitude and bound the rest.

def LP_property(*args):
    cases = []
    assert len(args) > 1, "Error: Littlewood-Paley constraints must involve at least two variables."
    for expr1, expr2 in itertools.combinations(args, 2):
        conjuncts = { expr1.asymp(expr2) }
        for other_expr in args:
            if not other_expr.defeq(expr1) and not other_expr.defeq(expr2):
                conjuncts.add(other_expr <= expr1)
        cases.append(And(*conjuncts))
    return Or(*cases)



