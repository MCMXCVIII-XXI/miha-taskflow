import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    yield container
    container.stop()


def test_container_works(postgres_container):
    url = postgres_container.get_connection_url()
    assert "postgresql" in url
