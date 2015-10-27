# encoding: utf-8
from equality import Equality

"""
    AST: 抽象语法树
    Imp 中有3种结构：算术表达式、布尔表达式和声明语句
    注意，Imp 中变量只能是数字，没有字符处理功能
"""


class Statement(Equality):
    pass


class Aexp(Equality):
    pass


class Bexp(Equality):
    pass


"""
    算术表达式，包括 3类：
    42(常数) 、 x(变量) 、 x + 42(二位操作)
"""


class IntAexp(Aexp):
    # 看到，我们要求构造函数中传入的就是 int，而不是 string
    def __init__(self, i):
        self.i = i

    def __repr__(self):
        return 'IntAexp(%d)' % self.i

    def eval(self, env):
        return self.i


class VarAexp(Aexp):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'VarAexp(%s)' % self.name

    # 可以理解为在声明空间中查找变量名
    def eval(self, env):
        if self.name in env:
            return env[self.name]
        else:
            # 不理解的变量，默认为 0
            return 0

arith_binops = {
    '+': lambda l, r: l + r,
    '-': lambda l, r: l - r,
    '*': lambda l, r: l * r,
    '/': lambda l, r: l / r,
}


class BinopAexp(Aexp):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return 'BinopAexp(%s, %s, %s)' % (self.op, self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        if self.op in arith_binops:
            value = arith_binops[self.op](left_value, right_value)
        else:
            raise RuntimeError('unknown operator: ' + self.op)
        return value


"""
    布尔表达式分 4 种：关系比较、与、或、非
"""
boolean_relops = {
    '<': lambda l, r: l < r,
    '<=': lambda l, r: l <= r,
    '>': lambda l, r: l > r,
    '>=': lambda l, r: l >= r,
    '=': lambda l, r: l == r,
    '!=': lambda l, r: l != r,
}


class RelopBexp(Bexp):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return 'RelopBexp(%s, %s, %s)' % (self.op, self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        if self.op in boolean_relops:
            value = boolean_relops[self.op](left_value, right_value)
        else:
            raise RuntimeError('unknown operator: ' + self.op)
        return value


class AndBexp(Bexp):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return 'AndBexp(%s, %s)' % (self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        return left_value and right_value


class OrBexp(Bexp):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return 'OrBexp(%s, %s)' % (self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        return left_value or right_value


class NotBexp(Bexp):
    def __init__(self, exp):
        self.exp = exp

    def __repr__(self):
        return 'NotBexp(%s)' % self.exp

    def eval(self, env):
        value = self.exp.eval(env)
        return not value


"""
    声明表达式也分4种，赋值、复合、条件、循环
"""


class AssignStatement(Statement):
    def __init__(self, name, aexp):
        self.name = name
        self.aexp = aexp

    def __repr__(self):
        return 'AssignStatement(%s, %s)' % (self.name, self.aexp)

    # 赋值的估值，就是在声明空间 env 中，记录这个变量
    def eval(self, env):
        value = self.aexp.eval(env)
        env[self.name] = value


class CompoundStatement(Statement):
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __repr__(self):
        return 'CompoundStatement(%s, %s)' % (self.first, self.second)

    def eval(self, env):
        self.first.eval(env)
        self.second.eval(env)


class IfStatement(Statement):
    def __init__(self, condition, true_stmt, false_stmt):
        self.condition = condition
        self.true_stmt = true_stmt
        self.false_stmt = false_stmt

    def __repr__(self):
        return 'IfStatement(%s, %s, %s)' % (self.condition, self.true_stmt, self.false_stmt)

    def eval(self, env):
        condition_value = self.condition.eval(env)
        if condition_value:
            self.true_stmt.eval(env)
        else:
            if self.false_stmt:
                self.false_stmt.eval(env)


class WhileStatement(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return 'WhileStatement(%s, %s)' % (self.condition, self.body)

    def eval(self, env):
        condition_value = self.condition.eval(env)
        while condition_value:
            self.body.eval(env)
            # 再次评估条件
            condition_value = self.condition.eval(env)
