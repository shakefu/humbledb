"""
This module contains version checking helpers.

"""
import pkg_resources

import pymongo


def _lt(version):
    """ Return ``True`` if ``pymongo.version`` is less than `version`.

        :param str version: Version string

    """
    return (pkg_resources.parse_version(pymongo.version) <
            pkg_resources.parse_version(version))


def _gte(version):
    """ Return ``True`` if ``pymongo.version`` is greater than or equal to
        `version`.

        :param str version: Version string

    """
    return (pkg_resources.parse_version(pymongo.version) >=
            pkg_resources.parse_version(version))


def _clean(kwargs):
    """ Mutate `kwargs` to handle backwards incompatible version discrepancies.

        Currently only changes the `safe` param into `w`. If ``safe=False`` is
        passed it is transformed into ``w=0``.

        Otherwise `safe` is removed from the args.
    """
    if _lt('3.0'):
        return

    if 'safe' not in kwargs:
        return

    if kwargs['safe'] == False:
        del kwargs['safe']
        kwargs['w'] = 0
        return

    del kwargs['safe']


