from sqlalchemy import text
from sqlalchemy.engine import Engine


def test_database_connection(test_engine: Engine):
    with test_engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    assert database_name == "articles_test"
