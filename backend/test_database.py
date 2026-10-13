
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine


def main():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT current_database(), version()")
            )

            database_name, version = result.one()

            print("Database connection successful!")
            print(f"Database: {database_name}")
            print(f"PostgreSQL: {version.split(',')[0]}")

    except SQLAlchemyError as error:
        print(f"Database connection failed: {type(error).__name__}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
