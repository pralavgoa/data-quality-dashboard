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
from mysql.connector import connect
from collections import Iterable
from dateutil import parser
from datetime import datetime, timedelta


connection_params = dict(host="dashdb.cpbiogsr5vhp.us-west-2.rds.amazonaws.com",    # your host, usually localhost
                     user="dqdash",         # your username
                     passwd="7fKWRj8UC0",   # your password
                     database="dashdb",     # name of the data base
                     connect_timeout=10)    # seconds
                     #use_pure=False)        # use C extension if False


def get_csv(header, data):
    res = io.StringIO()
    writer = csv.writer(res)
    if header:
        writer.writerow(header)
    for row in data:
        writer.writerow(row[:len(header)] if header else row)
    return res.getvalue()


def get_tab_data(tab):
    con = connect(**connection_params)
    cur = con.cursor()
    try:
        if tab == "tab1_a":
            parent_id = get_arg("parent_id")
            data_nodes = True if get_arg("data_nodes") == "true" else False

            data_nodes_q = "AND data_available BETWEEN 1 and 2" if data_nodes else ""
            try:
                parent_id = 0 if parent_id == "#" else int(parent_id)
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
                    else:
                        item["li_attr"] = {"class": "li_black",}
                    data.append(item)
                    data_d[ontology_id] = item
                # Check if has children
                if data:
                    query = "SELECT DISTINCT parent_id FROM tab1_a WHERE " + " OR ".join(("parent_id=%s" % (i,) for i in ids)) + ";"
                    cur.execute(query)
                    for i, in cur:
                        data_d[i]["children"] = True
                return Response(json.dumps(data).encode("utf8"), 200, mimetype="application/json")
            except ValueError:
                pass
            except TypeError as ex:
                pass

        elif tab == "tab1_b":
            try:
                ontology_id = int(get_arg("ontology_id"))
                min_year = int(get_arg("min_year") or "2000")
                max_year = int(get_arg("may_year") or "9999")

                cur.execute("""
                    SELECT query_run_timestamp,ontology_id,year,ucla,uci,ucsf,ucsd,ucd FROM tab1_b
                    WHERE ontology_id=%s
                    AND (year BETWEEN %s AND %s);""", [ontology_id, min_year, max_year])

                data = []
                header = "query_run_timestamp,ontology_id,year,ucla,uci,ucsf,ucsd,ucd".split(",")
                for row in cur:
                    item = dict()
                    for i,name in enumerate(header):
                        item[name] = row[i]
                    data.append(item)
                data = {
                    "result": "success",
                    "data": data
                }
                return data
            except ValueError:
                pass
        elif tab == "tab2_raw":
            try:
                year = int(get_arg("year", ""))
                month = int(get_arg("month", ""))
                day = int(get_arg("day", ""))
            except ValueError:
                return {"result": "error", "error_message": "Invalid parameter type", "code":"400"}

            if not year or not month or not day:
                return
            start = datetime(year, month, day)
            end = datetime(year, month, day+1)

            cur.execute("""
                SELECT path,timestamp,ucla,uci,ucd,ucsf,ucsd FROM dashdb.tab2_raw
                WHERE timestamp BETWEEN %s AND %s;""", [start.isoformat(), end.isoformat()])

            data = []
            for path,timestamp,ucla,uci,ucd,ucsf,ucsd in cur:
                item = dict(
                    path=path,
                    timestamp=timestamp,
                    ucla=ucla,
                    uci=uci,
                    ucd=ucd,
                    ucsf=ucsf,
                    ucsd=ucsd
                )
                data.append(item)
            data = dict(
                result="success",
                data = data
            )
            return data
        else:
            return dict(result="error", error_message="Specified data api not found", code=404)
    finally:
        cur.close()
        con.close()

    return dict(result="error", error_message="Unknown error", code=500)


def get_tab4_data():
    # External is 1 based, internal is 0 based

    per_page = int(get_arg("per_page", "15"))
    per_page = max(2, min(999, per_page))
    page = int(get_arg("page", "1"))
    page = max(0, page - 1)
    start = page * per_page

    con = connect(**connection_params)
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT site, issue, is_resolved FROM (
                SELECT * FROM tab4 ORDER BY row_id DESC LIMIT {p},{pp}
            ) sub
            ORDER BY row_id DESC;
        """.format(p=start, pp=per_page))
        rows = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM tab4 ORDER BY row_id")
        count = (cur.fetchall() or [[0]])[0][0]
        pages = ceil(count / per_page)
    finally:
        cur.close()
        con.close()

    return dict(page_count=pages, current_page=page+1, per_page=per_page, data=rows)


def set_comment(ontology_id, hospital, comment):
    con = connect(**connection_params)
    cur = con.cursor()
    try:
        if(get_comment(ontology_id, hospital)):
            # Set
            row_count = cur.execute("""
                SET SQL_SAFE_UPDATES = 0;
                UPDATE tab1_c
                SET comment=%s
                WHERE ontology_id=%s AND hospital=%s;
                SET SQL_SAFE_UPDATES = 1;""", [comment, ontology_id, hospital])
            con.commit()
        else:
            # Insert
            row_count = cur.execute("INSERT INTO tab1_c (ontology_id,hospital,comment) VALUES (%s,%s,%s)", [ontology_id, hospital, comment])
            con.commit()
    finally:
        cur.close()
        con.close()


def insert_comment(ontology_id, hospital, comment):
    is_public = 1 if session["role"] == "admin" else 0
    con = connect(**connection_params)
    cur = con.cursor()
    try:
        row_count = cur.execute("INSERT INTO tab1_c (ontology_id,hospital,comment,username,is_public) VALUES (%s,%s,%s,%s,%s)", [ontology_id, hospital, comment,session["user_name"], is_public])
        con.commit()
    finally:
        cur.close()
        con.close()


def update_comment_visibility(comment_id, is_public):
    # Make sure it's an integer for security
    comment_id = int(comment_id)
    is_public = int(is_public)
    con = connect(**connection_params)
    cur = con.cursor()
    try:
        cur.execute("""UPDATE tab1_c
                SET is_public=%s
                WHERE row_id=%s""" % (is_public, comment_id))
        con.commit()
    finally:
        cur.close()
        con.close()


def get_comment(ontology_id, hospital):
    con = connect(**connection_params)
    cur = con.cursor()
    try:
        cur.execute("SELECT comment FROM tab1_c WHERE ontology_id=%s AND hospital=%s", [ontology_id, hospital])
        comment = ""
        for row in cur:
            comment = row[0]
            return row[0]
    finally:
        cur.close()
        con.close()


def get_comments(ontology_id):
    con = connect(**connection_params)
    cur = con.cursor()
    try:
        if session["role"] == "admin":
            cur.execute("SELECT hospital,comment,username,is_public,row_id FROM tab1_c WHERE ontology_id=%s ORDER BY row_id DESC;", [ontology_id])
        else:
            cur.execute("SELECT hospital,comment,username,is_public,row_id FROM tab1_c WHERE (ontology_id=%s) AND (is_public=1 OR username=%s) ORDER BY row_id DESC;", [ontology_id, session["user_name"]])
        comments = []
        for row in cur:
            assert isinstance(row[3], (int, bool))
            item = dict()
            item["hospital"] = row[0]
            item["comment"] = row[1]
            item["username"] = row[2]
            item["is_public"] = True if row[3] else False
            item["id"] = row[4]
            comments.append(item)
    finally:
        cur.close()
        con.close()
    return comments


def test_db():
    from time import time
    query = "SELECT * FROM tab1_b"
    t = time()
    print(t)
    con = connect(**connection_params)
    cur = con.cursor()
    try:
        cur.execute(query)
        if 1:
            print(get_csv(None, cur))
        else:
            for row in cur:
                print(row)
    finally:
        cur.close()
        con.close()
    print(time()-t)


if __name__ == "__main__":
    test_db()
