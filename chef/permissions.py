class Permissions(object):
    """ Represents single permissions object with list of actors and groups """

    def __init__(self):
        self.actors = []
        self.groups = []

    def to_dict(self):
        d = {
            "actors": self.actors,
            "groups": self.groups
        }

        return d
