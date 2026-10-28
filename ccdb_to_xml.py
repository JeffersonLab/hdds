#!/usr/bin/env python3
#
# ccdb_to_xml.py - pull a complete set of HDDS geometry xml files out of
#                  CCDB (the /GEOMETRY records) for a given run and variation
#
# Usage: ccdb_to_xml.py [-r <run>] [-v <variation>] [-t <time>] [-d <dir>]
#                       [-f] [-l] [-u <url>] [<record> ...]
#
#   -r <run>        run number to look up (default 999999999, which finds
#                   records whose run range is open-ended)
#   -v <variation>  CCDB variation (default "default"); if a record has no
#                   assignment in this variation, the parent variation is
#                   used, as CCDB does for the simulation
#   -t <time>       take the constants as they were at this time, e.g.
#                   2025-06-30 or 2025-06-30_12:00:00 (default: latest)
#   -d <dir>        directory to write into (default: a new directory named
#                   ccdb_GEOMETRY_run<run>_<variation>); created if missing
#   -f              allow overwriting files that already exist in <dir>
#   -l              list what would be written, write nothing
#   -u <url>        CCDB connection string (default: $JANA_CALIB_URL, then
#                   $CCDB_CONNECTION)
#   <record>        pull only these records, e.g. main_HDDS.xml
#                   (default: every record in /GEOMETRY)
#
# Besides the xml files, <dir>/CCDB_MANIFEST.txt lists for each record the
# variation and run range it actually came from, the assignment id, its
# creation time and comment, and the md5 of the file written.
#
# This replaces the earlier python2 ccdb_to_xml.py, whose overwrite check
# never worked (the exit was caught by a bare except), so it silently
# replaced any existing files of the same names in the current directory.
#

import argparse
import hashlib
import os
import sys


def main():
    ap = argparse.ArgumentParser(
        description="Pull HDDS geometry xml files out of CCDB /GEOMETRY.")
    ap.add_argument("-r", "--run", type=int, default=999999999)
    ap.add_argument("-v", "--variation", default="default")
    ap.add_argument("-t", "--time", default=None,
                    help="constants as of this time, e.g. 2025-06-30")
    ap.add_argument("-d", "--dir", default=None)
    ap.add_argument("-f", "--force", action="store_true",
                    help="overwrite existing files in the output directory")
    ap.add_argument("-l", "--list", action="store_true",
                    help="only list what would be written")
    ap.add_argument("-u", "--url", default=None,
                    help="CCDB connection string")
    ap.add_argument("records", nargs="*")
    a = ap.parse_args()

    url = a.url or os.environ.get("JANA_CALIB_URL") or \
        os.environ.get("CCDB_CONNECTION")
    if not url:
        sys.exit("ccdb_to_xml.py: no CCDB connection: give -u <url> or set "
                 "JANA_CALIB_URL or CCDB_CONNECTION")
    try:
        import ccdb
    except ImportError:
        sys.exit("ccdb_to_xml.py: cannot import the ccdb python module; "
                 "set up the GlueX/CCDB environment first")

    provider = ccdb.AlchemyProvider()
    provider.connect(url)
    provider.authentication.current_user_name = "anonymous"

    directory = provider.get_directory("/GEOMETRY")
    if directory is None:
        sys.exit("ccdb_to_xml.py: no /GEOMETRY directory in %s" % url)
    tables = {t.name: t for t in provider.get_type_tables(directory)}
    names = a.records or sorted(tables)
    missing = [n for n in names if n not in tables]
    if missing:
        sys.exit("ccdb_to_xml.py: not in /GEOMETRY: %s" % " ".join(missing))

    outdir = a.dir or "ccdb_GEOMETRY_run%d_%s" % (a.run, a.variation)
    if not a.list:
        os.makedirs(outdir, exist_ok=True)
        clash = [n for n in names if os.path.exists(os.path.join(outdir, n))]
        if clash and not a.force:
            sys.exit("ccdb_to_xml.py: %d file(s) already exist in %s (e.g. "
                     "%s); nothing written. Use -f to overwrite."
                     % (len(clash), outdir, clash[0]))

    kw = {"date_and_time": a.time} if a.time else {}
    rows, failed = [], []
    for name in names:
        try:
            asg = provider.get_assignment(tables[name], a.run, a.variation,
                                          **kw)
        except Exception:
            failed.append(name)
            print("%-28s  no assignment for run %d, variation %s"
                  % (name, a.run, a.variation))
            continue
        data = asg.constant_set.data_table[0][0]
        rr = asg.run_range
        info = (name, asg.variation.name, rr.min, rr.max, asg.id,
                asg.created.strftime("%Y-%m-%d %H:%M:%S"),
                hashlib.md5(data.encode("utf-8")).hexdigest(),
                " ".join((asg.comment or "").split()))
        rows.append(info)
        print("%-28s  variation %-10s runs %d-%d  assignment %d  %s"
              % info[:6])
        if not a.list:
            with open(os.path.join(outdir, name), "w", encoding="utf-8",
                      newline="") as f:
                f.write(data)

    if not a.list and rows:
        with open(os.path.join(outdir, "CCDB_MANIFEST.txt"), "w") as f:
            f.write("# ccdb_to_xml.py run=%d variation=%s time=%s url=%s\n"
                    % (a.run, a.variation, a.time or "latest",
                       ccdb.hide_password(url)
                       if hasattr(ccdb, "hide_password") else url))
            f.write("# record\tvariation\trun_min\trun_max\tassignment"
                    "\tcreated\tmd5\tcomment\n")
            for r in rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        print("wrote %d file(s) and CCDB_MANIFEST.txt to %s"
              % (len(rows), outdir))
    if failed:
        print("%d record(s) had no assignment: %s" % (len(failed),
                                                      " ".join(failed)))
        sys.exit(2)


if __name__ == "__main__":
    main()
