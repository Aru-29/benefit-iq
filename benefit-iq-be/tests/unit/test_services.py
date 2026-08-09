from benefit_iq.api.dependencies.services import get_clickhouse_database
from benefit_iq.infrastructure.dependency_injection.container import init_container
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase


def test_container_instantiation():
    container = init_container()
    assert container is not None
    assert container.clickhouse is not None


def test_get_clickhouse_database_dependency():
    container = init_container()
    container.wire(modules=["benefit_iq.api.dependencies.services"])
    try:
        # Resolve via container
        db = container.clickhouse()
        assert isinstance(db, ClickHouseDatabase)
    finally:
        container.unwire()

