# encoding: utf-8

import sys
import re

RESERVED = 'RESERVED'  # 保留字
INT = 'INT'  # 整数
ID = 'ID'  # 字符

token_exprs = [
    (r'[ \n\t]+', None),  # 空格，tab，换行，无 tag
    (r'#[^\n]*', None),  # 注释，无 tag;  注释为 # 开头，后面跟若干个非换行的字符
    (r':=', RESERVED),
    (r'\(', RESERVED),
    (r'\)', RESERVED),
    (r';', RESERVED),
    (r'\+', RESERVED),
    (r'-', RESERVED),
    (r'\*', RESERVED),
    (r'/', RESERVED),
    (r'<=', RESERVED),
    (r'<', RESERVED),
    (r'>=', RESERVED),
    (r'>', RESERVED),
    (r'=', RESERVED),
    (r'!=', RESERVED),
    (r'and', RESERVED),
    (r'or', RESERVED),
    (r'not', RESERVED),
    (r'if', RESERVED),
    (r'then', RESERVED),
    (r'else', RESERVED),
    (r'while', RESERVED),
    (r'do', RESERVED),
    (r'end', RESERVED),
    (r'[0-9]+', INT),  # 无小数，只有整数
    (r'[A-Za-z][A-Za-z0-9_]*', ID),  # 字符开头后面为字符数字或下划线
]


def lex(characters, token_exprs):
    """
        lex 的工作方式，不是 split 开各个符号，然后逐一来检查
        而是首先要定义好全部可能的 pattern 的集合，也就是 token_exprs 数组
        然后，从头开始，循环遍历所有的 pattern，来看当前开头部分的字符是否 match
        如果 match，把位置挪到 match 部分之后，继续进行全部 pattern 的遍历 match
        也就是说，空格等特殊字符也必须对应 pattern，不然到了空格时就无法 match 了
        如果没有 match，报错退出
    """
    pos = 0
    tokens = []
    # 从头开始
    while pos < len(characters):
        match = None
        # 遍历 pattern 来做 match，tag 为该 pattern 的标签或标识
        for pattern, tag in token_exprs:
            regex = re.compile(pattern)
            match = regex.match(characters, pos)
            if match:
                # 只 match 一个，而不是 matchAll，故此只会取到一个
                text = match.group(0)
                # 如果有 tag，那么加入 tokens；
                # 否则呢？什么都不做，这种情况正好处理空格等特殊字符
                if tag:
                    token = (text, tag)
                    tokens.append(token)
                # match 到了，就退出 pattern 的遍历
                break
        if not match:
            sys.stderr.write('Illegal character: %sn' % characters[pos])
            sys.exit(1)
        # match 到了，就挪到匹配部分的下一个位置，继续循环
        else:
            pos = match.end(0)
    return tokens


def imp_lex(characters):
    return lex(characters, token_exprs)


if __name__ == '__main__':
    with open('imp_spec') as file:
        characters = file.read()
        tokens = imp_lex(characters)
        for token in tokens:
            print token
