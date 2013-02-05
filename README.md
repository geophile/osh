osh
===

Osh (Object SHell) is a command-line and API toolkit combining cluster access, database
access, and data slicing and dicing. Sort of like awk and cssh morsels
wrapped up in a Python crust.

Osh processes streams of Python objects using simple commands. Complex
data processing is achieved by command sequences in which the output
from one command is passed to the input of the next. This is similar
to composing Unix commands using pipes. However, Unix commands pass
strings from one command to the next, and the commands (grep, awk,
sed, etc.) are heavily string-oriented. Osh commands send primitive
Python types such as strings and numbers; composite types such as
tuples, lists and maps; objects representing files, dates and times;
or even user-defined objects.

Example (CLI)
=============

Suppose you have a cluster named fred, consisting of nodes 101, 102,
103. Each node has a database tracking work requests with a table
named request. You can find the total number of open requests in each
database as follows (using the CLI):

    jao@zack$ osh @fred [ sql "select count(*) from request where state = 'open'" ] ^ out
    ('101', 1)
    ('102', 0)
    ('103', 5)

* *osh*: Invokes the osh interpreter.

* *@fred [ ... ]*: fred is the name of a cluster, (configured in the osh configuration file, .oshrc). A thread is created for each node of the cluster, and the bracketed command run remotely on each, in parallel.
* *sql "select count(*) from request where state = 'open'"*: sql is an osh command that submits a query to a relational database. The query output is returned as a stream of tuples. 
* *^ out*: ^ is the osh operator for piping objects from one command to the next In this case, the input objects are tuples resulting from execution of a SQL query on each node of the cluster. The out command renders each object as a string and prints it to stdout.

Each output row identifies the node of origination (e.g. 101, 102),
and includes a tuple from the database on that node. So ('103', 5)
means that the database on node 103 has 5 open requests.

Example continued
-----------------

Now suppose you want to find the total number of open requests across
the cluster. You can pipe the (node, request count) tuples into an
aggregation command:

    jao@zack$ osh @fred [ sql "select count(*) from request where state = 'open'" ] ^ f 'node, count: count' ^ red + $
    6

* *f*: f is the osh command for function application. In this case, the function has two arguments, the node from which the count was obtained, and the count itself. This function returns just the count.
* *red +*: red is the reduction command. Input consists of counts from the nodes of the cluster. + is applied to combine the counts into a single number.
* *$*: An alternative to ^ out that can be used at the end of a command only.
* *6*: The total of the counts from across the cluster. 

Note that this example combines remote execution on cluster nodes, database access (on each cluster node), and data processing (the aggregation step) in a single framework.

Example (API)
=============

The same computation can be done using the API as follows:

    #!/usr/bin/python
    
    from osh.api import *
    
    osh(remote("fred",
             sql("select count(*) from request where state = 'open'")),
        f(lambda node, count: count),
        red(lambda x, y: x + y),
        out())

* *from osh.api import *: Imports the osh API.
* *osh(...)*: Invokes the osh interpreter.
* *remote("fred", sql(...)): Runs the sql command on each node of cluster fred, in parallel.
* *f(lambda node, count: count)*: To each (node, count) coming from the previous command, apply a function which discards the node identifier and keeps the count.
* *red(lambda x, y: x + y)*: Apply addition to the sequence of counts.
* *out()*: Print each input.

Installation
============

From source
-----------

    sudo python setup.py install

Using pip
---------

    sudo pip install osh

More information
================

* License: [GPL](LICENSE.txt)
* [Release history](http://geophile.com/osh/history.html)
* [User's Guide](http://geophile.com/osh/userguide)
* [Command Reference Guide](http://geophile.com/osh/ref)
* [Software with similar goals](http://geophile.com/osh/similar.html)
