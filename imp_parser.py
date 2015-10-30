# encoding: utf-8

import sys
from primitive import imp_parse
from lexer import imp_lex


def usage():
    sys.stderr.write('Usage: python imp_parser.py file')
    sys.exit(1)

def run():
    if len(sys.argv) != 2:
        usage()
    filename = sys.argv[1]
    text = open(filename).read()
    tokens = imp_lex(text)
    parse_result = imp_parse(tokens)
    if not parse_result:
        sys.stderr.write('Parse error !\n')
        sys.exit(1)
    ast = parse_result.value
    env = {}
    ast.eval(env)

    sys.stdout.write('Final variable values: \n')
    for name in env:
        sys.stdout.write("%s: %s\n" % (name, env[name]))

if __name__ == '__main__':
    run()
