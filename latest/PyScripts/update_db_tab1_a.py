import mysql.connector
from time import clock, time


def ask(prompt="", default=0):
    ans = input(prompt + " [y(es) | n(o) | c(ancel)]: ")
    if ans == "y" or ans == "yes":
        return 1
    elif ans == "n" or ans == "no":
        return 0
    elif ans == "c" or ans == "cancel":
        return -1
    else:
        return default


last_report = time()
counter = 0
def speed_reporter():
    global last_report, counter
    counter += 1
    new_time = time()
    delta = new_time - last_report
    if delta >= 1:
        print("Items/sec: %0.3f" % (counter / delta,))
        counter = 0
        last_report = new_time


db_writes = 0
def commit_counter(limit=10000):
    global db_writes
    db_writes += 1
    if db_writes >= limit:
        print("Commiting...")
        db.commit()
        print("Commit done.")
        db_writes = 0


connection_params = dict(host="dashdb.cpbiogsr5vhp.us-west-2.rds.amazonaws.com",    # your host, usually localhost
                     user="dqdash",         # your username
                     passwd="7fKWRj8UC0",   # your password
                     database="dashdb",     # name of the data base
                     connect_timeout=10,    #seconds
                     use_pure=False)        # use C extension if False

db = mysql.connector.connect(**connection_params)
db.autocommit = False
cur = db.cursor()

ans = ask("Reset all rows?")
if ans == 1:
    cur.execute("""
        UPDATE tab1_a
        SET data_available=0;""")
    cur.reset()
elif ans == -1:
    cur.close()
    db.close()
    exit()

ans = ask("Set available data?")
if ans == 1:
    cur.execute("SELECT ontology_id FROM tab1_b;")
    #cur.execute("SELECT ontology_id FROM tab1_b LIMIT 5;")
    ids = cur.fetchall()

    cur.execute("SET SQL_SAFE_UPDATES = 0;")
    cur.reset()

    for id, in ids:
        cur.execute("""
            UPDATE tab1_a
            SET data_available=1
            WHERE ontology_id='%s';""" % (id,))
        counter += 1
        speed_reporter()
        commit_counter()

    cur.execute("SET SQL_SAFE_UPDATES = 1;")
    cur.reset()
    db.commit()
elif ans == -1:
    cur.close()
    db.close()
    exit()

ans = ask("Set parents of children?")
if ans == 1:
    def set_parent(ontology_id=None):
        cur.execute("SELECT parent_id, data_available FROM tab1_a WHERE ontology_id=%s", [ontology_id])  # Get parent of this parent
        ids = cur.fetchall()
        if ids:
            if ids[0][1] == 0:
                # Update to 2(Data available in child node) only if it is not marked already
                cur.execute("UPDATE tab1_a SET data_available=2 WHERE ontology_id=%s", [ontology_id])  # Set this parent
                cur.reset()
                speed_reporter()
                commit_counter()

            for parent, *args in ids:  # Will have only one item if ontology_ids are distinct
                set_parent(parent)



    cur.execute("SELECT parent_id FROM tab1_a WHERE data_available=1;")
    ids = cur.fetchall()
    for parent, in ids:
        set_parent(parent)

    db.commit()

elif ans == -1:
    cur.close()
    db.close()
    exit()


cur.close()
db.close()