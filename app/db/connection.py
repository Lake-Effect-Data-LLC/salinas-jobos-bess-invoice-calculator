from sqlalchemy import create_engine, text


def get_engine(database_url):
    if not database_url:
        raise ValueError("DATABASE_URL is required to connect to Postgres.")

    return create_engine(database_url, future=True)


def check_connection(engine):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
