import pytest
from django.db import connections
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT\

db_name = connections.databases['default']['NAME']


def run_sql(sql):
    conn = psycopg2.connect(database='postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.fixture(scope='session')
def django_db_setup():
    from django.conf import settings

    settings.DATABASES['default']['NAME'] = 'the_copied_db'

    run_sql('DROP DATABASE IF EXISTS the_copied_db')
    run_sql('CREATE DATABASE the_copied_db TEMPLATE ' + db_name)

    yield

    for connection in connections.all():
        connection.close()

    run_sql('DROP DATABASE the_copied_db')
