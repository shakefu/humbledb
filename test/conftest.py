import logging
import re
from typing import Generator

import pyconfig
import pymongo
import pytest

import humbledb

from .util import database_name


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """
    Override default `docker-compose.yml` path.

    This is a `pytest-docker` fixture.
    """
    # TODO(shakefu): Figure out if this override is actually used

    return "docker-compose.yml"


def mongodb_ready(host, port):
    """Return a function that checks if MongoDB is ready."""

    def ping():
        try:
            with pymongo.timeout(0.1):
                client = pymongo.MongoClient(host, port)
                client.admin.command("ping")
        except pymongo.errors.ServerSelectionTimeoutError:
            return False
        return True

    return ping


@pytest.fixture(scope="session")
def mongodb_service(docker_ip, docker_services):
    """
    Ensure that MongoDB service is up and responsive.

    This is a `pytest-docker` fixture.
    """
    port = docker_services.port_for("mongodb", 27017)
    host = docker_ip

    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=mongodb_ready(host, port)
    )

    return host, port


@pytest.fixture(scope="session")
def mongodb_uri(mongodb_service: tuple[str, int]):
    """
    Return a MongoDB URI for the test service.

    This can be overridden by setting the pyconfig variable
    `humbledb.test.db.host` and `humbledb.test.db.port`.

    Args:
        mongodb_service (tuple[str, int]): _description_

    Yields:
        _type_: _description_
    """
    host, port = mongodb_service
    host = pyconfig.get("humbledb.test.db.host", host)
    port = pyconfig.get("humbledb.test.db.port", port)
    uri = "mongodb://{}:{}/{}".format(host, port, database_name())
    return uri


@pytest.fixture()
def mongodb(mongodb_service: tuple[str, int]) -> Generator[humbledb.Mongo, None, None]:
    """
    Return a MongoDB client for the test service.

    This fixture also drops all the dbs created attached to it.
    """
    host, port = mongodb_service

    class db(humbledb.Mongo):
        config_host = host
        config_port = port

    yield db

    # Drop all the dbs created attached to this fixture
    names = db.connection.list_database_names()
    for name in names:
        if name == "admin":
            continue
        db.connection.drop_database(name)


@pytest.fixture(scope="module")
def DBTest(
    mongodb_service: tuple[str, int],
) -> Generator[humbledb.Mongo, None, None]:
    """
    Return a DBTest class with the MongoDB connection details.
    """
    host, port = mongodb_service

    class DBTest(humbledb.Mongo):
        config_host = host
        config_port = port

    yield DBTest

    # Drop all the dbs created attached to this fixture
    names = DBTest.connection.list_database_names()
    for name in names:
        if name == "admin":
            continue
        DBTest.connection.drop_database(name)


@pytest.fixture()
def enable_sharding(DBTest):
    """Enable sharding for `collection`."""

    def _enable_sharding(collection, key):
        conn = DBTest.connection
        try:
            conn.admin.command("listShards")
        except humbledb.errors.OperationFailure as exc:
            if re.match(".*no such.*listShards", str(exc)):
                logging.getLogger(__name__).info("Sharding not available.")
                return False
            raise
        try:
            conn.admin.command("enableSharding", database_name())
        except humbledb.errors.OperationFailure as exc:
            if "already" not in str(exc):
                raise
        try:
            conn.admin.command(
                "shardCollection", database_name() + "." + collection, key=key
            )
        except humbledb.errors.OperationFailure as exc:
            if "already" not in str(exc):
                raise
        logging.getLogger(__name__).info(
            "Sharding enabled for %r.%r on %r.", database_name(), collection, key
        )
        return True

    return _enable_sharding
