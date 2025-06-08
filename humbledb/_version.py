"""
This module contains version checking helpers.

"""

from importlib.metadata import version as get_version

from packaging.version import Version


def _lt(version):
    """Return ``True`` if ``pymongo.version`` is less than `version`.

    :param str version: Version string

    """
    pymongo_version = get_version("pymongo")
    return Version(pymongo_version) < Version(version)


def _gte(version):
    """Return ``True`` if ``pymongo.version`` is greater than or equal to
    `version`.

    :param str version: Version string

    """
    pymongo_version = get_version("pymongo")
    return Version(pymongo_version) >= Version(version)


def _clean(kwargs):
    """Mutate `kwargs` to handle backwards incompatible version discrepancies.

    Currently only changes the `safe` param into `w`. If ``safe=False`` is
    passed it is transformed into ``w=0``.

    Otherwise `safe` is removed from the args.
    """
    if _lt("3.0"):
        return

    if "safe" not in kwargs:
        return

    if kwargs["safe"] is False:
        del kwargs["safe"]
        kwargs["w"] = 0
        return

    del kwargs["safe"]
