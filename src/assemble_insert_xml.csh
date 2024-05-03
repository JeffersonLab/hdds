#/bin/tcsh
root -b -q make_insert_xml.C
cat insert_preamble.xml pwo.xml insert_volume_defs.xml > CrystalECAL_HDDS.xml

