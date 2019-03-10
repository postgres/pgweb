from django.db import connection


def exec_to_dict(query, params=None):
    curs = connection.cursor()
    curs.execute(query, params)
    columns = [col[0] for col in curs.description]
    return [dict(list(zip(columns, row))) for row in curs.fetchall()]
