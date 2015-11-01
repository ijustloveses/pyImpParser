# encoding: utf-8


class Result:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __repr__(self):
        return 'Result(%s, %d)' % (self.value, self.pos)


class Parser:
    def __call__(self, tokens, pos):
        pass  # subclass will override it

    # + 并排组合算子，返回一个复合 parser
    def __add__(self, other):
        return Concat(self, other)

    # * 列表左递归组合算子
    def __mul__(self, other):
        return Exp(self, other)

    # | 或组合算子
    def __or__(self, other):
        return Alternate(self, other)

    # ^ 结果操纵组合算子
    def __xor__(self, function):
        return Process(self, function)


class Reserved(Parser):
    """
        保留字解析器，对应一个保留字 token (value / tag)
        如果传入的 tokens 流以及指定位置上的 token 是匹配的
        那么生成结果为本 token 的 value 和下一个 token 的位置
    """
    def __init__(self, value, tag):
        self.value = value
        self.tag = tag

    def __call__(self, tokens, pos):
        if pos < len(tokens) and tokens[pos][0] == self.value and \
                tokens[pos][1] is self.tag:
            return Result(tokens[pos][0], pos + 1)
        else:
            return None


class Tag(Parser):
    """
        Tag 解析器比起保留字解析器更宽松，只对应一个 tag
        只要传入 tokens 流以及指定位置上的 token 的 tag 匹配
        那么，生成结果为本 token 的 value 和下一个 token 位置
        对应字符和数字，不限制具体值是什么，只要 tag 是 INT 或 ID 即可
    """
    def __init__(self, tag):
        self.tag = tag

    def __call__(self, tokens, pos):
        if pos < len(tokens) and tokens[pos][1] is self.tag:
            return Result(tokens[pos][0], pos + 1)
        else:
            return None


class Concat(Parser):
    """
        合并两个 Parser，先左后右的顺序返回被合并的 Parser
        1+2 ==> Concat(Concat(Tag(INT), Reserved('+', RESERVED)), Tag(INT))
        or Tag(INT) + Reserved('+', RESERVED) + Tag(INT)
    """
    # 看到， Concat(x, y) 其实是构造函数生成一个新的 Parser 实例
    # 而不是函数调用
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, tokens, pos):
        # 先调用左边，再调用右边
        left_result = self.left(tokens, pos)
        if left_result:
            right_result = self.right(tokens, left_result.pos)
            if right_result:
                combined_value = (left_result.value, right_result.value)
                return Result(combined_value, right_result.pos)
        return None


class Alternate(Parser):
    """
        实现 or 的功能，先左后右，左成功则结束，否则分会右结果
        就是说从左到右以此解析，一旦能解析，则跳出
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, tokens, pos):
        # 先调用左边，再调用右边
        left_result = self.left(tokens, pos)
        if left_result:
            return left_result
        else:
            # 注意看，仍然回到 pos 来调用右边 parser，当作左边没有发生过
            return self.right(tokens, pos)


class Opt(Parser):
    """
        强制使用本 parser 解析，如果失败，则返回 None value，并恢复 pos
        注意，失败的返回值是 Result(None, pos), 而不是 None，返回是成功的，
        只是不消耗标记符，结果的位置仍然保持在输入位置
    """
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, tokens, pos):
        result = self.parser(tokens, pos)
        if result:
            return result
        else:
            return Result(None, pos)


class Rep(Parser):
    """
        使用本 parser 循环调用 tokens，直到调用失败；
        返回最后一次成功调用的下一个位置 (result.pos)
    """
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, tokens, pos):
        results = []
        result = self.parser(tokens, pos)
        # 考虑到上面的 Opt，如果失败 pos 置回原位
        # 但是 Opt 失败时不返回 None，而是返回 Result(None, pos)
        # 故此，Rep(Opt(xxx)) 这个组合可能会导致无尽循环
        while result:
            results.append(result.value)
            pos = result.pos
            result = self.parser(tokens, pos)
        return Result(results, pos)


class Process(Parser):
    """
        使用本 parser 调用 tokens 之后再对结果做一次 function 调用
        有了它，就可以对各 parser 返回的字符串结果进行估值等有实际意义的操作
    """
    def __init__(self, parser, function):
        self.parser = parser
        self.function = function

    def __call__(self, tokens, pos):
        result = self.parser(tokens, pos)
        if result:
            result.value = self.function(result.value)
        return result    # could be none


class Lazy(Parser):
    """
        所谓 Lazy，就是直到被调用时，才会通过初始化时传入的 parser_func 生成 parser
        parser_func 不接受任何参数，生成一个 parser 解析器
    """
    def __init__(self, parser_func):
        self.parser = None
        self.parser_func = parser_func

    def __call__(self, tokens, pos):
        if not self.parser:
            self.parser = self.parser_func()
        return self.parser(tokens, pos)


class Phrase(Parser):
    """
        本 parser 必须要消耗所有剩余的标记符，使得整个待解析字符完整被解析
        否则失败
        这将是最上层的一个解析器，防止我们解析不完整的输入字符
    """
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, tokens, pos):
        result = self.parser(tokens, pos)
        if result and result.pos == len(tokens):
            return result
        else:
            return None


class Exp(Parser):
    """
        参数为两个解析器，一个用来解析列表元素，一个用来解析分隔符
        采用左递归，从左到右依次调用解析器
    """
    def __init__(self, parser, separator):
        self.parser = parser
        self.separator = separator

    def __call__(self, tokens, pos):
        # 先用本 parser 对最左边的一段解析
        result = self.parser(tokens, pos)

        def process_next(parsed):
            # sepfunc 是 self.separator 解析的结果； right 是 self.parser 解析的结果
            (sepfunc, right) = parsed
            # 然后使用 sepfunc 把左边和右边的结果结合，故此 separator 不能是个简单的字符串，而应该是个解析器
            return sepfunc(result.value, right)

        # 剩下的部分，使用 separator + parser 解析，举个例子
        # 'a ; b ; c'  -->  最开始解析了 'a'  --> 然后到这里，解析 '; + b'
        # 那么 '; + b' 得到的 value 应该是 (;, b), pos 应该走到第二个 ';' 那里
        # 然后，利用 ^ 对 (;, b) 进行 process_next 调用
        next_parser = self.separator + self.parser ^ process_next   # 先 + 再 ^
        next_result = result

        while next_result:
            next_result = next_parser(tokens, result.pos)
            if next_result:
                result = next_result
        return result


if __name__ == '__main__':
    import lexer
    s = 'a ; b ; c'
    tokens = lexer.imp_lex(s)
    # output: [('a', 'ID'), (';', 'RESERVED'), ('b', 'ID'), (';', 'RESERVED'), ('c', 'ID')]
    print tokens

    parser = Tag('ID')
    result = parser(tokens, 0)
    # output Result(a, 1)
    print result

    separator = Reserved(';', 'RESERVED')

    def post_proc(parsed):
        (left, right) = parsed
        # output: left:  ;
        print 'left: ', left
        # output: right:  b
        print 'right: ', right
        return (left, right)
    np1 = separator + parser
    np2 = separator + parser ^ post_proc
    res1 = np1(tokens, result.pos)
    # output: Result((';', 'b'), 3)
    print res1
    res2 = np2(tokens, result.pos)
    # output: Result((';', 'b'), 3)
    print res2
