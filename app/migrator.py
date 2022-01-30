import os
from argparse import ArgumentParser

from yoyo import get_backend, read_migrations

from app.settings import settings


def get_back():
    backend = get_backend(settings.pg_dsn)
    return backend


def get_migrations():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    migrations_path = os.path.join(dir_path, "migrations")
    migrations = read_migrations(migrations_path)
    print(migrations)

    return migrations


def apply():
    backend = get_back()
    migrations = get_migrations()

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def rollback_last():
    backend = get_back()
    migrations = get_migrations()

    with backend.lock():
        backend.rollback_one(migrations[-1])


if __name__ == "__main__":
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--rollback", action="store_true")
    group.add_argument("-a", "--apply", action="store_true")

    args = parser.parse_args()
    if args.rollback:
        rollback_last()
    elif args.apply:
        apply()
