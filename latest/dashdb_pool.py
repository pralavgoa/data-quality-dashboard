import csv
import io
import json
import mysql.connector
import os
from flask import request, Response, session
from helpers import get_arg
from mysql.connector.errors import *
from mysql.connector.errorcode import *
from math import ceil
from time import time
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import connect


connection_params = dict(host="dashdb.cpbiogsr5vhp.us-west-2.rds.amazonaws.com",    # your host, usually localhost
                     user="dqdash",         # your username
                     passwd="7fKWRj8UC0",   # your password
                     database="dashdb",     # name of the data base
                     connect_timeout=10)    # seconds
                     #use_pure=False)        # use C extension if False

pool = MySQLConnectionPool(pool_size=5, **connection_params)


def get_csv(header, data):
    res = io.StringIO()
    writer = csv.writer(res)
    if header:
        writer.writerow(header)
    for row in data:
        writer.writerow(row[:len(header)] if header else row)
    return res.getvalue()

cur = "a"
def execute(*args, **kwargs):
    pass
def fetch_all(*args, **kwargs):
    pass
def fetch_iter(*args, **kwargs):
    pass


def get_tab_data(tab):
    if tab == "tab1_a":
        parent_id = get_arg("parent_id")
        data_nodes = True if get_arg("data_nodes") == "true" else False

        data_nodes_q = "AND data_available BETWEEN 1 and 2" if data_nodes else ""
        try:
            parent_id = 0 if parent_id == "#" else int(parent_id)
            con = pool.get_connection()
            cur = con.cursor()
            try:
                cur.execute("""
                    SELECT ontology_id,parent_id,ontology_name, data_available FROM tab1_a
                    WHERE parent_id=%s {dn};""".format(dn=data_nodes_q), [parent_id])
                data = []
                data_d = dict()
                ids = []
                for ontology_id, parent_id, ontology_name, data_available in cur:
                    ids.append(ontology_id)
                    item = dict(
                        id=ontology_id,
                        parent="#" if parent_id == 0 else parent_id,
                        text=ontology_name,
                        children=False,

                    )
                    if data_available == 1:
                        item["li_attr"] = {"class": "li_darkblue",}
                    elif data_available == 2 and not data_nodes:
                        item["li_attr"] = {"class": "li_darkgreen",}
                    data.append(item)
                    data_d[ontology_id] = item
                # Check if has children
                if data:
                    query = "SELECT DISTINCT parent_id FROM tab1_a WHERE " + " OR ".join(("parent_id=%s" % (i,) for i in ids)) + ";"
                    cur.execute(query)
                    for i, in cur:
                        data_d[i]["children"] = True
            finally:
                pool.add_connection()

            return Response(json.dumps(data).encode("utf8"), 200, mimetype="application/json")
        except ValueError:
            pass
        except TypeError as ex:
            pass

    elif tab == "tab1_b":
        try:
            ontology_id = int(get_arg("ontology_id"))
            min_year = int(get_arg("min_year") or "2000")
            max_year = int(get_arg("may_year") or "2050")

            execute("""
                SELECT * FROM tab1_b
                WHERE ontology_id=%s
                AND (year BETWEEN %s AND %s);""", ontology_id, min_year, max_year)
            return get_csv(["query_run_timestamp", "ontology_id", "Year", "UCLA", "UCI", "UCSF", "UCSD", "UCD"], cur)
        except ValueError:
            pass

    return None


def get_tab4_data():
    # External is 1 based, internal is 0 based

    per_page = int(get_arg("per_page", "2"))
    per_page = max(2, min(999, per_page))
    page = int(get_arg("page", "1"))
    page = max(0, page - 1)
    start = page * per_page

    execute("""
        SELECT site, issue, is_resolved FROM (
            SELECT * FROM tab4 ORDER BY row_id DESC LIMIT {p},{pp}
        ) sub
        ORDER BY row_id DESC;
    """.format(p=start, pp=per_page))
    rows = fetch_all()

    execute("SELECT COUNT(*) FROM tab4 ORDER BY row_id")
    count = (fetch_all() or [[0]])[0][0]
    pages = ceil(count / per_page)

    return dict(page_count=pages, current_page=page+1, per_page=per_page, data=rows)


def set_comment(ontology_id, hospital, comment):
    if(get_comment(ontology_id, hospital)):
        # Set
        row_count = execute("""
            SET SQL_SAFE_UPDATES = 0;
            UPDATE tab1_c
            SET comment=%s
            WHERE ontology_id=%s AND hospital=%s;
            SET SQL_SAFE_UPDATES = 1;""", comment, ontology_id, hospital)
    else:
        # Insert
        row_count = execute("INSERT INTO tab1_c (ontology_id,hospital,comment) VALUES (%s,%s,%s)", ontology_id, hospital, comment)


def insert_comment(ontology_id, hospital, comment):
    is_public = 1 if session["role"] == "admin" else 0
    row_count = execute("INSERT INTO tab1_c (ontology_id,hospital,comment, is_public) VALUES (%s,%s,%s,%s)", ontology_id, hospital, comment, is_public)

def update_comment_visibility(comment_id, is_public):
    # Make sure it's an integer for security
    comment_id = int(comment_id)
    is_public = int(is_public)
    execute("""UPDATE tab1_c
            SET is_public=%s
            WHERE row_id=%s""", is_public, comment_id)


def get_comment(ontology_id, hospital):
    execute("SELECT comment FROM tab1_c WHERE ontology_id=%s AND hospital=%s", ontology_id, hospital)
    comment = ""
    for row in fetch_iter():
        comment = row[0]
        return row[0]


def get_comments(ontology_id):
    if session["role"] == "admin":
        execute("SELECT hospital,comment, is_public, row_id FROM tab1_c WHERE ontology_id=%s ORDER BY row_id DESC;", ontology_id)
    else:
        execute("SELECT hospital,comment FROM tab1_c WHERE (ontology_id=%s) AND (is_public=1) ORDER BY row_id DESC;", ontology_id)
    comments = []
    for row in fetch_iter():
        item = {"hospital": row[0], "comment": row[1]}
        if session["role"] == "admin":
            assert isinstance(row[2], (int, bool))
            item["is_public"] = True if row[2] else False
            item["id"] = row[3]
        comments.append(item)
    return comments


def test_db():
    from time import time
    query = "SELECT * FROM tab1_b"
    t = time()
    print(t)
    execute(query)
    if 1:
        print(get_csv(None, fetch_iter()))
    else:
        for row in fetch_iter():
            print(row)
    print(time()-t)


if __name__ == "__main__":
    test_db()
    cur.close()
    db.close()
