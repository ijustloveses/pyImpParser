# encoding: utf-8

from lexer import *
from parser import *
from ast import *

# Basic parsers
def keyword(kw):
    """
        Imp 的关键字就是保留字，RESERVED 标签
        返回 Reserved 对象，即是说，keyword 函数也类似 Parser 的构造函数
    """
    return Reserved(kw, RESERVED)

"""
    num 和 id 都是 Parser 对象
    其中，num 是 Tag(INT) 构造的 Tag Parser 又跟了一个后续操作，把字符转为 int
    注意，num 只是个包含了这些操作定义的 Parser 对象，真正的转换在调用 num('xx') 时
"""
num = Tag(INT) ^ (lambda i: int(i))
id = Tag(ID)


"""
    数学表达式部分
"""
def aexp_value():
    """
        使用 | 即 Alternate Parser，先看左边也即是否能解析为整数表达式
        如果不能，再看右边是否成立，也即是否能解析为变量表达式
        整个还是一个 Parser，这个 Parser 解析时得到的 Result 的 value 是个表达式
    """
    return (num ^ (lambda i: IntAexp(i))) | \
           (id  ^ (lambda v: VarAexp(v)))

def aexp_group():
    """
        匹配括号，先把 (、aexp、) 三部分调用 Concat，得到 ('(', aexp), ')')
        然后把结果过给 process_group 函数调用，后者见下面，其实就是提取出 aexp
        至于 aexp 是什么，后面有定义
        而，之所以用 Lazy，是因为 aexp 会调用 aexp_group ，这样会形成无限递归
        故此，使用 Lazy，直到真正调用去解析某个实际输入时，才会真正调用 aexp
    """
    return keyword('(') + Lazy(aexp) + keyword(')') ^ process_group

def process_group(parsed):
    ((_, p), _) = parsed
    return p

def aexp_term():
    """
        定义 aexp_term，要么是整数/变量，要么是括号
    """
    return aexp_value() | aexp_group()

def process_binop(op):
    """
        二元运算符 op，那么返回一个 op 决定的二元运算表达式
        本函数是个高阶函数，返回的表达式需要传入左右两个参数表达式
    """
    return lambda l, r: BinopAexp(op, l, r)

def any_operator_in_list(ops):
    """
        给定一组操作符，转成 keyword，也即 Reserved(op)
        然后，从左到右一次匹配，一旦匹配，返回被匹配的那个操作符
        故此，也是一个解析器的生成器，或者直接视为解析器
    """
    op_parsers = [keyword(op) for op in ops]
    parser = reduce(lambda l, r: l | r, op_parsers)
    return parser

# Operator keywords and precedence levels
# 优先级由高到低的，每个优先级都有一个操作符列表
aexp_precedence_levels = [
    ['*', '/'],
    ['+', '-'],
]

# An IMP-specific combinator for binary operator expressions (aexp and bexp)
def precedence(value_parser, precedence_levels, combine):
    """
        value_parser 是一个解析器，可以读取 aexp_term，也就是数字、变量、括号
        precedence_levels 就是优先级由高到低的，不同优先级为一个子列表的列表
    """
    def op_parser(precedence_level):
        """
            precedence_level，单数的，就是给定某一个优先级下的操作符列表
            要做的事情是生成一个新的解析器，这个解析器的作用是：
            对操作符列表逐一匹配，匹配到了之后，再对 value 调用 combine
        """
        return any_operator_in_list(precedence_level) ^ combine

    """
        下面使用 * 操作符，其实就是 Exp 组合子
        从优先级最高的开始解析，并循环处理所有优先级的操作符
    """
    parser = value_parser * op_parser(precedence_levels[0])
    for precedence_level in precedence_levels[1:]:
        parser = parser * op_parser(precedence_level)
    return parser

def aexp():
    """
        就是说 combine 取 process_binop，value_parser 取 aexp_term
        precedence_levels 取 aexp_precedence_levels
    """
    return precedence(aexp_term(),
                      aexp_precedence_levels,
                      process_binop)


"""
    逻辑表达式部分
"""
def bexp_not():
    """
        Not 表达式，同样需要 lazy，是因为 bexp_term 实际上包括 bexp_not，避免循环调用
    """
    return keyword('not') + Lazy(bexp_term) ^ (lambda parsed: NotBexp(parsed[1]))

def process_relop(parsed):
    ((left, op), right) = parsed
    return RelopBexp(op, left, right)

def bexp_relop():
    """
        比较表达式
    """
    relops = ['<', '<=', '>', '>=', '=', '!=']
    return aexp() + any_operator_in_list(relops) + aexp() ^ process_relop

def bexp_group():
    """
       括号表达式，lazy是因为 bexp 包括 bexp_group
    """
    return keyword('(') + Lazy(bexp) + keyword(')') ^ process_group

def bexp_term():
    """
        逻辑表达式基本组成部分：not、比较、括号
    """
    return bexp_not()   | \
           bexp_relop() | \
           bexp_group()

def process_logic(op):
    """
        基本组成部分由 and / or 来连接
    """
    if op == 'and':
        return lambda l, r: AndBexp(l, r)
    elif op == 'or':
        return lambda l, r: OrBexp(l, r)
    else:
        raise RuntimeError('unknown logic operator: ' + op)

bexp_precedence_levels = [
    ['and'],
    ['or'],
]

def bexp():
    """
        类似数学表达式，使用 Exp 组合算子来按优先级递归调用表达式
    """
    return precedence(bexp_term(),
                      bexp_precedence_levels,
                      process_logic)


"""
    声明语句
"""
def assign_stmt():
    """
        赋值语句
    """
    def process(parsed):
        ((name, _), exp) = parsed
        return AssignStatement(name, exp)
    return id + keyword(':=') + aexp() ^ process

def stmt_list():
    """
        组合语句，使用 Exp 组合子
        separator 是一个高阶函数，分隔符左右来组成组合语句
    """
    separator = keyword(';') ^ (lambda x: lambda l, r: CompoundStatement(l, r))
    return Exp(stmt(), separator)

def if_stmt():
    """
        麻烦点在于 else 是可选的，故此：
        process 中判断了 false_parsed 是否存在
        返回值中使用了 Opt(keyword('else'))
    """
    def process(parsed):
        (((((_, condition), _), true_stmt), false_parsed), _) = parsed
        if false_parsed:
            (_, false_stmt) = false_parsed
        else:
            false_stmt = None
        return IfStatement(condition, true_stmt, false_stmt)
    return keyword('if') + bexp() + \
           keyword('then') + Lazy(stmt_list) + \
           Opt(keyword('else') + Lazy(stmt_list)) + \
           keyword('end') ^ process

def while_stmt():
    """
        循环体中是一个 stmt_list
    """
    def process(parsed):
        ((((_, condition), _), body), _) = parsed
        return WhileStatement(condition, body)
    return keyword('while') + bexp() + \
           keyword('do') + Lazy(stmt_list) + \
           keyword('end') ^ process

def stmt():
    return assign_stmt() | \
           if_stmt()     | \
           while_stmt()


"""
    外层 wrapper 语句
"""
# Top level parser
def imp_parse(tokens):
    ast = parser()(tokens, 0)
    return ast

def parser():
    """
        一个程序只不过是一个语句列表
        Phrase组合子保证我们用到了文件的每一个标记符
    """
    return Phrase(stmt_list())


if __name__ == '__main__':
    s = '4 * 5 + (6 + 1)'
    tokens = imp_lex(s)
    print tokens
    result = imp_parse(tokens)
    print result
