#!/usr/bin/env python3
"""Material_HDDS.xml = the repo file + materials_klf.xml + materials_scaled.xml"""
import os
base = open('/home/halld/hdds/Material_HDDS.xml').read()
add = open('materials_klf.xml').read()
if os.path.exists('materials_scaled.xml'):
    add += open('materials_scaled.xml').read()
j = base.rindex('</materials>')
open('Material_HDDS.xml', 'w').write(base[:j] + add + '\n' + base[j:])
