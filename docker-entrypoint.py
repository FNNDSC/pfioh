#!/usr/bin/env python3

# Single entry point / dispatcher for simplified running of
#
## pman
## pfioh
## purl
#

import  argparse
import  os

str_desc = """

 NAME

    docker-entrypoint.py

 SYNOPSIS

    docker-entrypoint.py    [optional cmd args for pfioh]


 DESCRIPTION

    'docker-entrypoint.py' is the main entry point for running the pfioh container.

"""

# def pman_do(args, unknown):
#
#     str_otherArgs   = ' '.join(unknown)
#
#     str_CMD = "/usr/local/bin/pman %s" % (str_otherArgs)
#     return str_CMD

def pfioh_do(args, unknown):

    str_otherArgs   = ' '.join(unknown)

    str_CMD = "/usr/bin/pfioh --forever %s" % (str_otherArgs)
    return str_CMD

# def purl_do(args, unknown):
#
#     str_http        = http_construct(args, unknown)
#     str_otherArgs   = ' '.join(unknown)
#
#     str_raw = ''
#     if args.b_raw: str_raw = "--raw"
#
#     str_CMD = "/usr/local/bin/purl --verb %s %s %s --jsonwrapper '%s' --msg '%s' %s" % (args.verb, str_raw, str_http, args.jsonwrapper, args.msg, str_otherArgs)
#     return str_CMD

# def bash_do(args, unknown):
#
#     str_http        = http_construct(args, unknown)
#     str_otherArgs   = ' '.join(unknown)
#
#     str_CMD = "/bin/bash"
#     return str_CMD


parser  = argparse.ArgumentParser(description = str_desc)

# parser.add_argument(
#     '--pman',
#     action  = 'store_true',
#     dest    = 'b_pman',
#     default = False,
#     help    = 'if specified, indicates transmission to a linked <pman> container.',
# )
# parser.add_argument(
#     '--pfioh',
#     action  = 'store_true',
#     dest    = 'b_pfioh',
#     default = False,
#     help    = 'if specified, indicates transmission to a linked <pfioh> container.',
# )
parser.add_argument(
    '--msg',
    action  = 'store',
    dest    = 'msg',
    default = '',
    help    = 'JSON msg payload'
)

# parser.add_argument(
#     '--jsonwrapper',
#     action  = 'store',
#     dest    = 'jsonwrapper',
#     default = '',
#     help    = 'wrap msg in optional field'
# )
# parser.add_argument(
#     '--raw',
#     help    = 'if specified, do not wrap return data from remote call in json field',
#     dest    = 'b_raw',
#     action  = 'store_true',
#     default = False
# )


args, unknown   = parser.parse_known_args()

if __name__ == '__main__':
    try:
        fname   = 'pfioh_do(args, unknown)'
        str_cmd = eval(fname)
        # print(str_cmd)
        os.system(str_cmd)
    except:
        print("Misunderstood container app... exiting.")
