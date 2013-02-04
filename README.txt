==================
Object Shell (osh)
==================

Version 1.0.3.

REQUIREMENTS
============

**Operating system:** Osh has been tested on various Fedora and Ubuntu
releases, as well as OS X.  The process module and management of
remote processes relies on the /proc filesystem, so these facilities
do not work on OS X.

**Python:** Osh requires Python 2.3 or later. 



INSTALLATION
============

Using pip
---------

    sudo pip install osh

sudo is necessary.

From source
-----------

1. Unpackage the tarball: tar xzvf osh-1.0.3.tar.gz.

2. cd into the osh-1.0.3 directory.

3. Do the installation: sudo -E python ./setup.py install

Testing the installation
------------------------

1. cd /usr/share/osh/test

2. Run: ./testall_cli. Output should look something like this::

    gen and out
    f
    select
    agg
    sort
    expand
    squish
    window
    unique
    stdin and sh
    builtins
    pipeline

Also run ./testall_api. Output should look like this::

    gen and out
    f (lambda)
    f (string)
    select (lambda)
    select (string)
    agg (lambda)
    agg (string)
    agg group (lambda)
    agg group (string)
    agg consecutive (lambda)
    agg consecutive (string)
    sort (lambda)
    sort (string)
    expand
    expand (position)
    expand (negative position)
    squish (0-1)
    squish (>1)
    window (default)
    window (disjoint)
    window (overlap)
    window (predicate function)
    window (predicate string)
    unique
    unique (consecutive)
    sh
    builtin ifelse
    pipeline 1
    pipeline 2
    pipeline 3
    pipeline 4
    error handling (default)
    f#153[<function <lambda> at 0x722bf0>](1) exceptions.ZeroDivisionError: integer division or modulo by zero
    error handling (overridden)

WHAT INSTALLATION DOES
======================

* osh executables are placed in /usr/bin.

* The python scripts implementing osh are placed in site-packages/osh
under your python installation's directory.

* Documentation is placed in /usr/share/doc/osh.

* The osh tests, scripts, and installation tarball are placed in /usr/share/osh.


BUG REPORTS AND SUGGESTIONS
===========================

Jack Orenstein
jao@geophile.com
