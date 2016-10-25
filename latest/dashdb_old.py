import MySQLdb
import csv
import io
import json
from flask import request, Response
from helpers import get_arg

# Needs apt python3-mysqldb

db = MySQLdb.connect(host="dashdb.cpbiogsr5vhp.us-west-2.rds.amazonaws.com",    # your host, usually localhost
                     user="dqdash",         # your username
                     passwd="7fKWRj8UC0",  # your password
                     db="dashdb",           # name of the data base
                     connect_timeout=10)   #seconds

db.autocommit(True)


def get_csv(header, data):
    res = io.StringIO()
    writer = csv.writer(res)
    if header:
        writer.writerow(header)
    for row in data:
        writer.writerow(row[:len(header)] if header else row)
    return res.getvalue()


def get_tab_data(tab):
    cur = db.cursor()
    if tab == "tab1_a":
        parent_id = get_arg("parent_id")
        try:
            parent_id = 0 if parent_id == "#" else int(parent_id)
            cur.execute("""
            SELECT ontology_id,parent_id,ontology_name FROM tab1_a
            WHERE parent_id=%s""", [parent_id]) # WHERE parent_id=%s
            data = []
            for ontology_id, parent_id, ontology_name in cur.fetchall():
                data.append(dict(
                    id=ontology_id,
                    parent="#" if parent_id == 0 else parent_id,
                    text=ontology_name,
                    children=True
                ))
                #data.append(dict(id=9999999,text="placeholder", parent=ontology_id))
            return Response(json.dumps(data).encode("utf8"), 200, mimetype="application/json")
        except ValueError:
            pass
        except TypeError:
            pass

    elif tab == "tab1_b":
        try:
            ontology_id = int(get_arg("ontology_id"))
            min_year = int(get_arg("min_year") or "2005")
            max_year = int(get_arg("may_year") or "2016")

            cur.execute("""
                SELECT * FROM tab1_b
                WHERE ontology_id=%s
                AND (year BETWEEN %s AND %s)""", [ontology_id, min_year, max_year])
            return get_csv(["query_run_timestamp", "ontology_id", "Year", "UCLA", "UCI", "UCSF", "UCSD", "UCD"], cur.fetchall())
        except ValueError:
            pass

    elif tab == "tab1_c":
        cur.execute("SELECT * FROM tab1_c")
        return get_csv(["ontology_id", "hospital", "comments"], cur.fetchall())

    cur.close()
    return None


def set_comment(ontology_id, hospital, comment):
    cur = db.cursor()
    if(get_comment(ontology_id, hospital)):
        row_count = cur.execute("""
            SET SQL_SAFE_UPDATES = 0;
            UPDATE tab1_c
            SET comment=%s
            WHERE ontology_id=%s AND hospital=%s;""", [comment, ontology_id, hospital])
    else:
        row_count = cur.execute("INSERT INTO tab1_c (ontology_id,hospital,comment) VALUES (%s,%s,%s)", [ontology_id, hospital, comment])
    cur.close()


def get_comment(ontology_id, hospital):
    cur = db.cursor()
    cur.execute("SELECT comment FROM tab1_c WHERE ontology_id=%s AND hospital=%s", [ontology_id, hospital])
    comment = ""
    for row in cur.fetchall():
        comment = row[0]
        cur.close()
        return row[0]


def get_comments(ontology_id):
    cur = db.cursor()
    cur.execute("SELECT hospital,comment FROM tab1_c WHERE ontology_id=%s", [ontology_id])
    comments = []
    for row in cur.fetchall():
        comments.append({"hospital": row[0], "comment": row[1]})
    cur.close()
    return comments


def test_db():
    from time import time
    query = "SELECT * FROM tab1_b"
    t = time()
    print(t)
    cur = db.cursor()
    cur.execute(query)
    if 1:
        print(get_csv(None, cur.fetchall()))
    else:
        for row in cur.fetchall():
            print(row)
    cur.close()
    print(time()-t)


if __name__ == "__main__":
    test_db()
    db.close()