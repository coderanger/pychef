import pkg_resources
from chef.api import ChefAPI
from chef.exceptions import ChefObjectTypeError, ChefObjectNameError
from chef.permissions import Permissions


class Acl(object):
    """Represents an ACL rules for the chef objects."""

    ace_types = ["create", "read", "update", "delete", "grant"]
    object_types = ["clients", "containers", "cookbooks", "data", "environments", "groups", "nodes", "roles"]

    """ ALC API available only in Chef server from version 12.0"""
    version = pkg_resources.parse_version("12.0.0")

    def __init__(self, object_type, name, api, skip_load=False):
        self._check_object_type(object_type)

        self.object_type = object_type
        self.name = name
        self.url = "/%s/%s/_acl/" % (object_type, name)
        self.api = api or ChefAPI.get_global()

        self.attributes_map = {}
        for t in self.ace_types:
            self.attributes_map[t] = Permissions()

        if not skip_load:
            self.reload()

    @property
    def create(self):
        """ Gets Create permissions """
        return self.attributes_map["create"]

    @property
    def read(self):
        """ Gets Read permissions """
        return self.attributes_map["read"]

    @property
    def update(self):
        """ Gets Update permissions """
        return self.attributes_map["update"]

    @property
    def delete(self):
        """ Gets Delete permissions """
        return self.attributes_map["delete"]

    @property
    def grant(self):
        """ Gets Grant permissions """
        return self.attributes_map["grant"]

    def save(self):
        """ Save updated permissions objects to the Chef server """
        for t in self.ace_types:
            self.api.api_request('PUT', self.url + t, data={t: self[t]})

    def __getitem__(self, key):
        if key in self.attributes_map.keys():
            return self.attributes_map[key]
        else:
            return {}

    def reload(self):
        """ Load current permissions for the object """
        data = self.api.api_request('GET', self.url)
        for t in self.ace_types:
            self[t].actors = data[t]['actors']
            self[t].groups = data[t]['groups']

    def to_dict(self):
        d = {}
        for t in self.ace_types:
            d[t] = self[t].to_dict()

        return d

    def _check_object_type(self, object_type):
        if object_type not in self.object_types:
            raise ChefObjectTypeError('Object type %s is not allowed' % object_type)

    def is_supported(self):
        return self.api.version_parsed >= self.version
