from chef.api import ChefAPI
from chef.base import ChefObject

class Client(ChefObject):
    """A Chef client object."""

    url = '/clients'

    def _populate(self, data):
        self.platform = self.api and self.api.platform
        self.private_key = None
        if self.platform:
            self.orgname = data.get('orgname')
            self.validator = bool(data.get('validator', False))
            self.public_key = data.get('public_key')
            self.admin = False
        else:
            self.admin = bool(data.get('admin', False))
            self.public_key = data.get('public_key')
            self.orgname = None
            self.validator = False

    @property
    def certificate(self):
        return self.public_key

    def to_dict(self):
        d = super(Client, self).to_dict()
        d['json_class'] = 'Chef::ApiClient'
        if self.platform:
            d.update({
                'orgname': self.orgname,
                'validator': self.validator,
                'public_key': self.certificate,
                'clientname': self.name,
            })
        else:
            d.update({
                'admin': self.admin,
                'public_key': self.public_key,
            })
        return d

    @classmethod
    def create(cls, name, api=None, admin=False):
        api = api or ChefAPI.get_global()
        obj = cls(name, api, skip_load=True)
        obj.admin = admin
        d = api.api_request('POST', cls.url, data=obj)
        obj.private_key = d['private_key']
        obj.public_key = d['public_key']
        return obj

    def rekey(self, api=None):
        api = api or self.api
        d_in = {'name': self.name, 'private_key': True}
        d_out = api.api_request('PUT', self.url, data=d_in)
        self.private_key = d_out['private_key']
