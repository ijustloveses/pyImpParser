# encoding: utf-8

import sys
from primitive import imp_parse
from lexer import imp_lex


def run():
    text = 's := 4 ; t := s - 5'
    tokens = imp_lex(text)
    print 'tokens: ', tokens
    parse_result = imp_parse(tokens)
    print 'result_stmt and pos: ', parse_result
    if not parse_result:
        sys.stderr.write('Parse error !\n')
        sys.exit(1)
    ast = parse_result.value
    env = {}
    ast.eval(env)
    print 'eval result: ', env

    sys.stdout.write('Final variable values: \n')
    for name in env:
        sys.stdout.write("%s: %s\n" % (name, env[name]))

if __name__ == '__main__':
    run()
