#!/usr/bin/env python
#
# Example of how to pull a complete set of hdds geometry xml
# files from ccdb, given a run number and var string.
#

import os
import sys

def usage():
    print "Usage: ccdb_to_xml.py [-f] [-v <var>] [-r <run>] [<record>]"
    print "    where -f means overwrite existing files, if any;"
    print "    if <var> is not given, default is assumed;"
    print "    if <run> is not given, highest defined run is assumed;"
    print "    if <record> is not given, all GEOMETRY records are pulled."
    sys.exit(0)

if __name__ == "__main__":
    
    import ccdb
    from ccdb import Directory, TypeTable, Assignment, ConstantSet

    var = "default"
    run = 999999999
    force = False
    record = ""
    iarg = 1;
    while iarg < len(sys.argv):
        if sys.argv[iarg][0] == '-':
            if len(sys.argv) < iarg + 2:
                usage()
            elif sys.argv[iarg][1] == 'v':
                var = sys.argv[iarg+1];
                iarg += 2
                continue
            elif sys.argv[iarg][1] == 'r':
                run = sys.argv[iarg+1];
                iarg += 2
                continue
            elif sys.argv[iarg][1] == 'f':
                force = True
                iarg += 1
                continue
            else:
                usage()
        else:
            record = sys.argv[iarg]
            break

    sqlite_connect_str = os.environ["JANA_CALIB_URL"]        # Should be set!

    # create CCDB api class
    provider = ccdb.AlchemyProvider()                        # this class has all CCDB manipulation functions
    provider.connect(sqlite_connect_str)                     # use usual connection string to connect to database
    provider.authentication.current_user_name = "anonymous"  # to have a name in logs

    # read directory
    directory = provider.get_directory("/GEOMETRY")

    # returned directory is python object
    assert (isinstance(directory, Directory))

    for table in directory.type_tables:
        if record and record != table.name:
            continue
        assignment = provider.get_assignment(table, run, var)
        print "Writing", table.name, "variation", assignment.variation,
        print "run range", assignment.run_range.min, "-", assignment.run_range.max
        xmlstring = assignment.constant_set.data_table[0][0]
        try:
            fname = table.name
            f = open(fname)
            if force:
                f = open(fname, "w")
            else:
                print "Error - cannot overwrite existing file {0}".format(fname),
                print ", rerun with -f option to force."
                sys.exit(1)
        except:
            f = open(fname, "w")
        f.write(xmlstring)
        f.close()
