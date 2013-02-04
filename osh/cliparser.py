# osh
# Copyright (C) Jack Orenstein <jao@geophile.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# Dynamically generated code in tpg doesn't work right with "import external.tpg.tpg"
from external.tpg.tpg import * 

import loader
import core

core.osh_usage = core.USAGE_CLI

# SPACE is a character that must not occur in a typed-in command. It is introduced between command-line
# arguments to represent a separator to the osh parser. The value of SPACE must be consistent with
# both occurrences in the grammar:
# - In the "separator space" definition.
# - In the "token string" definition.
SPACE = '\v'

class _CLIParser(VerboseParser):
    """
        separator space '\v+';

        token at         '@';
        token comma      ',';
        token empty_list '\[\]';
        token begin      '\[';
        token end        '\]';
        token pipe       '\^';
        token dollar     '\$';
        token merge      '//';
        token string     '[^\v]+';

        START/c ->
            COMMAND/c
            (dollar                     $ op = load_op('out')
                                        $ op.add_arg('-t')
                                        $ op.add_arg('%s')
                                        $ op.args_done()
                                        $ c.pipeline().append_op(op)
            )?
            ;


        COMMAND/c ->
            dollar                      $ stdin = load_op('stdin')
                                        $ pipeline = core.Pipeline(stdin)
                                        $ out = load_op('out')
                                        $ out.add_arg('-t')
                                        $ out.add_arg('%s')
                                        $ out.args_done()
                                        $ pipeline.append_op(out)
                                        $ c = core.Command(pipeline)
            |
            pipe
                                        $ generator = load_op('stdin')
            PIPELINE/p                  $ c = core.Command(p.prepend_op(generator))
            |
            PIPELINE/p                  $ c = core.Command(p)
            ;

        PIPELINE/p ->
            OP/op                       $ p = core.Pipeline(op)
            (   pipe
                OP/op                   $ p = p.append_op(op)
            )*
            ;

        OP/op ->
            (
                OP_NAME/n               $ op = load_op(n)
                (    ARG/a              $ op = op.add_arg(a)
                )*                      $ op = op.args_done()
            |
                begin
                PIPELINE/p              $ op = p
                end
            |
                FORK/f                  $ op = load_op('fork')
                                        $ op = op.add_arg(f)
                begin
                PIPELINE/p              $ op = op.add_arg(p)
                (
                    MERGE/m             $ op = op.add_arg(m)
                )?
                end                     $ op = op.args_done()
            )
            ;

        OP_NAME/n ->
            string/n
            ;

        FORK/f -> 
           at
           string/s                     $ f = s
           ;

        MERGE/m ->
            merge                       $ m = 'x: x'
            (string/s                   $ m = s
            )?
            ;

        ARG/a ->
            empty_list                  $ a = '[]'
            |
            string/a
            |
            begin
            PIPELINE/a
            end
            ;
    """

    verbose = 0

def trace(message, object):
    print '%s(%s)' % (message, object)
    return object

def load_op(op_name):
    return loader.load_and_create(op_name)

def parse(command):
    return _CLIParser()(command)

