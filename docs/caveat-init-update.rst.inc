Initializing & Updating
-----------------------

When initializing or updating a bidict,
mappings where different keys map to a repeat value will be silently dropped,
just as dicts silently drop mappings for repeat keys
(e.g. ``{1: 'one', 1: 'uno'}`` becomes ``{1: 'uno'}``)::

    >>> nils = bidict(zero=0, zilch=0, zip=0)
    >>> len(nils)
    1
    >>> nils.update(nix=0, nada=0)
    >>> len(nils)
    1

This is considered acceptable because it is consistent with dict's behavior.
