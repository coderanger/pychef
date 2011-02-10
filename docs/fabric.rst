.. module:: chef.fabric
.. _fabric:

Fabric Integration
==================

PyChef offers a library to use Chef roles and nodes in a fabfile::

    from fabric.api import env, run, roles
    from chef.fabric import chef_roledefs

    env.roledefs = chef_roledefs()

    @roles('web_app')
    def mytask():
        run('uptime')
