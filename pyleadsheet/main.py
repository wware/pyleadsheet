"""
pyleadsheet -- convert a chordpro-like file into a pretty pdf leadsheet

Usage:
    pyleadsheet generate <inputfile> [options]
    pyleadsheet generate <inputdir> [options]
    pyleadsheet help

Options:
    -h            print this help screen
    --output=DIR  directory to place html files in (default: output)
    --format=EXT  right now only html is supported, pdf in the future
"""

import os
import docopt
from .parser import parse_file
from .renderer import render_song


def generate(args):

    inputfiles = []
    if os.path.isfile(args['<inputfile>']):
        inputfiles.append(args['<inputfile>'])
    elif os.path.isdir(args['<inputfile>']):
        for filename in os.listdir(args['<inputfile>']):
            if filename.lower().endswith('.yaml') or filename.lower().endswith('.yml'):
                inputfiles.append(os.path.join(args['<inputfile>'], filename))

    if not inputfiles:
        raise IOError('could not find input: ' + args['<inputfile>'])

    outputdir = args['--output'] or 'output'
    for yamlfile in inputfiles:
        render_song(parse_file(yamlfile), outputdir)

    return 0


def main():
    args = docopt.docopt(__doc__)

    if args['help']:
        print(__doc__)
        return 0

    elif args['generate']:
        return generate(args)
