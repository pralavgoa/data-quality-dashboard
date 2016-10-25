import mysql.connector
import json
from time import clock, time
from collections import deque, namedtuple


connection_params = dict(host="dashdb.cpbiogsr5vhp.us-west-2.rds.amazonaws.com",    # your host, usually localhost
                     user="dqdash",         # your username
                     passwd="7fKWRj8UC0",   # your password
                     database="dashdb",     # name of the data base
                     connect_timeout=10,    #seconds
                     use_pure=False)        # use C extension if False


"""
TEST environment changes
475622  ucla    big_change
478337  uci     big_change
475606  missing oid
475624  missing count uci
"""


class TableConnection(object):
    def __init__(self, table, execute=True):
        self.conn = mysql.connector.connect(**connection_params)
        self.cur = self.conn.cursor(buffered=False)
        self.cache = deque()
        self.table_name = table
        self.fetch_batch = 500
        if execute:
            self.execute()

    def execute(self):
        self.cur.execute("""SELECT ontology_id,year,ucla,uci,ucsf,ucsd,ucd FROM dashdb.`%s` ORDER BY ontology_id, year ASC""" % (self.table_name,))

    def skip(self, oid):
        while 1:
            # Remove all fetched rows that match
            while self.cache:
                row = self.cache[0]
                if row[0] == oid:  # Ontology equals
                    self.cache.popleft()
                else:
                    return
            self.cache.extend(self.cur.fetchmany(self.fetch_batch))
            if not self.cache:
                return


    def fetch_iter(self, oid):
        while 1:
            while self.cache:
                row = self.cache[0]
                if row[0] == oid:  # Ontology equals
                    self.cache.popleft()
                    yield row
                else:
                    return
            self.cache.extend(self.cur.fetchmany(self.fetch_batch))
            if not self.cache:
                return

    def close(self):
        pass
        #self.cur.reset()
        #self.cur.close()
        #self.conn.close()


last_report = time()
counter = 0
start_time = None
full_counter = 0
def speed_reporter(end=False):
    global last_report, counter, start_time, full_counter
    if end:
        if not start_time:
            return
        total_time = last_report - start_time
        per_second = full_counter / (total_time or 1)
        print("Average ontology's/sec: %0.3f" % (per_second,))
        print("Total operation time[seconds]: %i" % (total_time,))

    if not start_time:
        start_time = time()
    counter += 1
    full_counter += 1
    new_time = time()
    delta = new_time - last_report
    if delta >= 1:
        print("Ontology's/sec: %0.3f" % (counter / delta,))
        counter = 0
        last_report = new_time
        return True


def upload_results(stats, ontology_results):
    db = mysql.connector.connect(**connection_params)
    db.autocommit = False
    cur = db.cursor()

    missing_oids_message = """Ontologies are missing from previous run for ids:\n\n%s"""
    significant_change_message = """Data changed significantly from previous run for ids:\n\n%s"""
    missing_counts_message = """Counts are missing from previous run for ids:\n\n%s"""

    def process(type, message):
        rows = []
        clinics = dict()
        for k, v in ontology_results.items():  # k=ontology_id
            if v[type]:
                clinic = clinics.setdefault(v["affected_items"][0]["clinic"], [])
                clinic.append(k)
        for clinic, oids in clinics.items():
            oids = map(lambda x: str(x), oids)
            rows.append([clinic, message % (",".join(oids),)])
        return rows

    # Processing missing_oids
    clinic_names = "ucla,uci,ucsf,ucsd,ucd".split(",")
    missing_oids_rows = []
    for clinic in clinic_names:
        oids = map(lambda x: str(x), stats["missing_oids"])
        missing_oids_rows.append([clinic, missing_oids_message % (",".join(oids),)])

    # Processing significant_changes
    significant_change_rows = process("big_change", significant_change_message)

    # Processing missing_counts
    missing_counts_rows = process("missing_count", missing_counts_message)


    q = []
    for row in missing_oids_rows + significant_change_rows + missing_counts_rows:
        q.append("INSERT INTO tab4 (site,issue) VALUES ('%s','%s');" % (row[0], row[1]))
    q = "\n".join(q)
    for _ in cur.execute(q, multi=True):
        pass



    db.commit()
    cur.close()
    db.close()


def check_db(old_table, new_table):
    """

    :param old_table:
    :param new_table:
    :return:
    """
    db = mysql.connector.connect(**connection_params)
    db.autocommit = False
    cur = db.cursor()

    # Getting all ontology's
    print("Fetching ontology ids")
    old_table_oids = []
    # TODO remove DB ORDER-ing, currently used for debugging
    cur.execute("SELECT DISTINCT ontology_id FROM dashdb.`%s` ORDER BY ontology_id ASC LIMIT 1000" % (old_table,))
    for ontology_id, in cur.fetchall():
        old_table_oids.append(ontology_id)

    old_table_oids = sorted(old_table_oids)

    cur.close()
    db.close()

    # Preparing tables for comparison
    print("Preparing multiple connections")
    table_conns = [TableConnection(table) for table in [old_table, new_table]]

    # Fetch ontologies and compare counts
    stats = {
        "missing_oids_count": 0,
        "missing_years_count": 0,
        "missing_counts_count": 0,
        "big_changes_count": 0,

        "missing_oids": [],
        "missing_years": [],
        "missing_counts": [],
        "big_changes": [],
    }
    ontology_results = dict()

    print("Comparing counts")
    clinic_names = "ucla,uci,ucsf,ucsd,ucd".split(",")
    for oid in old_table_oids:
        table_data = []
        # Fetching data
        for table in table_conns:
            try:
                data = list(table.fetch_iter(oid))
            except:
                return
            table_data.append(data)

        if not table_data[0]:
            print("Old table has changed! please restart the script")
            continue

        # Check if oid missing in new table
        if not table_data[1]:
            stats["missing_oids"].append(oid)
            stats["missing_oids_count"] += 1
            continue


        # Generating params for detailed year comparison by check_ontology()
        params = [dict() for _ in table_data]
        for table_index, table in enumerate(table_data):
            for ontology, year, *clinics in table:  # table contains rows
                for i, name in enumerate(clinic_names):
                    years = params[table_index].setdefault(name, dict())
                    years.setdefault(year, clinics[i])

        if speed_reporter():
            pass

        result = check_ontology(*params)
        if result["big_change"]:
            stats["big_changes_count"] += 1
            stats["big_changes"].append(oid)

        if result["missing_year"]:
            stats["missing_years_count"] += 1
            stats["missing_years"].append(oid)

        if result["missing_clinic"]:
            stats["missing_clinics_count"] += 1
            stats["missing_clinics"].append(oid)

        if result["missing_count"]:
            stats["missing_counts_count"] += 1
            stats["missing_counts"].append(oid)

        # Save result if problems found
        if True in result.values():
            ontology_results[oid] = result

    for conn in table_conns:
        conn.close()
    print("End reached")
    print(json.dumps(stats, indent=4))
    print("Ontology results len:", len(ontology_results))
    print(json.dumps(ontology_results, indent=4))
    upload_results(stats, ontology_results)
    return


def check_ontology(old_data, new_data):
    """
    LOGIC:
    IF old_count > 0 AND new_count <= 0:
        missing_count = True
    IF old_count > 0 AND new_count > 0:
        IF abs(old_count - new_count) > 20%:
            Significant change

    :param old_data:
        {
            "uci":{
                2016:0,
            }
        }
    :param new_data:
        {
            "uci":{
                2016:0,
            }
        }
    :returns:
        {
            "missing_count": bool,
            "missing_year": bool,
            "big_change": bool,
            "affected_items": [],
        }
    """
    results = {
        "missing_count": False,
        "missing_year": False,
        "missing_clinic": False,
        "big_change": False,
        "affected_items": [],
    }


    # Checking
    trigger_change = 0.2
    for clinic, years in old_data.items():
        for year, count in years.items():
            # Check misssing clinic
            if clinic not in new_data:
                results["missing_clinic"] = True
                results["affected_items"].append({
                    "clinic": clinic,
                    "year": year,
                })
                continue

            # Check missing years
            if year not in new_data[clinic]:
                results["missing_year"] = True
                results["affected_items"].append({
                    "clinic": clinic,
                    "year": year,
                })
                continue

            # Check missing counts in new data( <= 0 )
            new_count = new_data[clinic][year]
            if count > 0 >= new_count:  # if old_count available(>0) and new_count not available(<=0)
                results["missing_count"] = True
                results["affected_items"].append({
                    "clinic": clinic,
                    "year": year,
                })
                continue

            # Ignore zero counts
            if count == 0 and new_count == 0:
                continue # Ignore

            # Check significant changes (20%)
            change = abs(count - new_count)
            if change / max(count, new_count) >= trigger_change:
                results["big_change"] = True
                results["affected_items"].append({
                    "clinic": clinic,
                    "year": year,
                })

    return results


def test():
    fails = 0

    def r(old, new, **kwargs):
        nonlocal fails
        res = check_ontology(old, new)
        d = {"old": old, "new": new}
        d.update(kwargs)
        print("test:", d)
        print("result:", res)
        for key, val in res.items():
            if isinstance(val, bool) and kwargs.get(key, False) != val:
                print("FAIL")
                print("---")
                fails += 1
                return
        print("OK")
        print("---")

    r({"a":{2016:3}},{"a":{2016:0}}, missing_count=True)
    r({"a":{2016:3}},{"a":{2016:8}}, big_change=True)
    r({"a":{2016:8}},{"a":{2016:3}}, big_change=True)
    r({"a":{2016:800}},{"a":{2016:800}})
    print("Fails:", fails)


#test()
check_db("tab1_b", "tab1_b_2016-10-11")
speed_reporter(True)
