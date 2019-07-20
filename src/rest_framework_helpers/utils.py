class HashableDict(dict):
    """
    Hashable Dictionary

    Hashables should be immutable -- not enforcing this but TRUSTING you not to mutate
    a dict after its first use as a key.

    https://stackoverflow.com/questions/1151658/python-hashable-dicts
    """

    def ___key___(self):
        return tuple((k, self[k]) for k in sorted(self))

    def __hash__(self):
        return hash(self.___key___())

    def __eq__(self, other):
        return self.___key___() == other.___key___()
