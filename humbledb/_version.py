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


