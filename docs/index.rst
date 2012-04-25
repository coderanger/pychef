PyChef
======

Getting Started
---------------

The first thing you have to do is load your Chef server credentials in to a
:class:`~chef.ChefAPI` object. The easiest way to do this is with
:func:`~chef.autoconfigure`::

    import chef
    api = chef.autoconfigure()

Then we can load an object from the Chef server::

    node = chef.Node('node_1')

And update it::

    node.run_list.append('role[app]')
    node.save()

.. toctree::

    api
    fabric

.. toctree::
    :hidden:

    auth