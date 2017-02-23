PyChef
======

.. image:: https://secure.travis-ci.org/coderanger/pychef.svg?branch=master
    :target: http://travis-ci.org/coderanger/pychef

A Python API for interacting with a Chef server.

Example
-------

::

    from chef import autoconfigure, Node
    
    api = autoconfigure()
    n = Node('web1')
    print n['fqdn']
    n['myapp']['version'] = '1.0'
    n.save()

Further Reading
---------------

For more information check out http://pychef.readthedocs.org/en/latest/index.html
