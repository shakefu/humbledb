import pymongo
import pytest
from tenacity import retry, stop_after_delay, wait_fixed


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """
    Override default `docker-compose.yml` path.

    This is a `pytest-docker` fixture.
    """
    return "docker-compose.yml"


@pytest.fixture(scope="session")
def mongodb_service(docker_ip, docker_services):
    """
    Ensure that MongoDB service is up and responsive.

    This is a `pytest-docker` fixture.
    """
    port = docker_services.port_for("mongodb", 27017)
    host = docker_ip

    @retry(stop=stop_after_delay(30), wait=wait_fixed(1))
    def _wait_for_mongo():
        client = pymongo.MongoClient(host, port, serverSelectionTimeoutMS=1000)
        client.admin.command("ping")

    _wait_for_mongo()

    return host, port


@pytest.fixture(scope="session", autouse=True)
def configure_db_test(mongodb_service):
    """
    Configure the DBTest class with the MongoDB connection details.
    """
    from .util import DBTest

    host, port = mongodb_service
    DBTest.config_host = host
    DBTest.config_port = port


@pytest.fixture(autouse=True)
def db_cleanup(mongodb_service):
    """
    Ensure the database is clean after each test.
    """
    from .util import DBTest, database_name

    yield

    with DBTest:
        DBTest.connection.drop_database(database_name())
