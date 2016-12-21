
import os
import sys
import subprocess
import glob
import SCons

# XML files included in main_HDDS.xml (and others) that scons can't figure out for itself
XMLDEPS = ['BarrelEMcal_HDDS.xml' , 'ForwardEMcal_HDDS.xml' , 'Solenoid_HDDS.xml'     ,
           'BeamLine_HDDS.xml'    , 'StartCntr_HDDS.xml'    , 'CentralDC_HDDS.xml'    ,
		   'ForwardTOF_HDDS.xml'  , 'Target_HDDS.xml'       , 'ComptonEMcal_HDDS.xml' ,
		   'Material_HDDS.xml'    , 'DIRC_HDDS.xml'         , 'PairSpect_HDDS.xml'    ,
		   'ForwardDC_HDDS.xml'   , 'Regions_HDDS.xml']

# Get command-line options
SHOWBUILD = ARGUMENTS.get('SHOWBUILD', 0)

# Get platform-specific name
osname = os.getenv('BMS_OSNAME', 'build')

# Check for GDML support in ROOT
hasGDMLsupport = False
rootsys = os.getenv('ROOTSYS')  # needed to run root to generate GDML
if rootsys != None:
	if os.path.exists('%s/include/TGDMLWrite.h' % rootsys): hasGDMLsupport = True
if hasGDMLsupport:
	print 'ROOT GDML support found. GDML files will be generated.'
else:
	print 'No ROOT support for GDML. GDML files will NOT be generated.'

# Setup initial environment
builddir   = ".%s" % (osname)
installdir = "#%s" %(osname)
include    = "%s/include" % (installdir)
bin        = "%s/bin" % (installdir)
lib        = "%s/lib" % (installdir)
env = Environment(ENV = os.environ,  # Bring in full environement, including PATH
                  CXX         = os.getenv('CXX', 'c++'),
                  CC          = os.getenv('CC' , 'cc'),
                  FC          = os.getenv('FC' , 'gfortran'),
                  CPPPATH     = ['.'])

# Add Xerces
xerces = os.getenv('XERCESCROOT')
if xerces == None:
	print 'You MUST have your XERCESCROOT environment variable defined!'
	sys.exit(-1)
env.AppendUnique(CPPPATH=['%s/include' % xerces])
env.AppendUnique(LIBPATH=['%s/lib' % xerces], LIBS=['xerces-c'])

# Use terse output unless otherwise specified
if SHOWBUILD==0:
	env.Replace(   CCCOMSTR       = "Compiling  [$SOURCE]",
				  CXXCOMSTR       = "Compiling  [$SOURCE]",
				  FORTRANPPCOMSTR = "Compiling  [$SOURCE]",
				  FORTRANCOMSTR   = "Compiling  [$SOURCE]",
				  SHCCCOMSTR      = "Compiling  [$SOURCE]",
				  SHCXXCOMSTR     = "Compiling  [$SOURCE]",
				  LINKCOMSTR      = "Linking    [$TARGET]",
				  SHLINKCOMSTR    = "Linking    [$TARGET]",
				  ARCOMSTR        = "Archiving  [$TARGET]",
				  RANLIBCOMSTR    = "Ranlib     [$TARGET]",
				  INSTALLSTR      = "Installing [$TARGET]")


# Turn on debug symbols and warnings
env.PrependUnique(      CFLAGS = ['-g', '-fPIC', '-Wall'])
env.PrependUnique(    CXXFLAGS = ['-g', '-fPIC', '-Wall'])
env.PrependUnique(FORTRANFLAGS = ['-g', '-fPIC'])

# Common source files used for all programs
COMMONSRC = ['hddsCommon.cpp', 'XParsers.cpp', 'XString.cpp', 'md5.c']

# Define source files for each program
HDDSGEANTSRC = ['hdds-geant.cpp' ] + COMMONSRC
HDDSROOTSRC  = ['hdds-root.cpp'  ] + COMMONSRC
HDDSROOTHSRC = ['hdds-root_h.cpp'] + COMMONSRC
HDDSMD5SRC   = ['hdds-md5.cpp'   ] + COMMONSRC
FINDALLSRC   = ['findall.cpp', 'hddsBrowser.cpp'] + COMMONSRC

# Prepend build directory to all sources so the .o files will
# be stored in the platform specific build dir
env.VariantDir(".%s" % (osname), '#', duplicate=0) 
HDDSGEANTSRC = [builddir + '/' + s for s in HDDSGEANTSRC]
HDDSROOTSRC  = [builddir + '/' + s for s in HDDSROOTSRC ]
HDDSROOTHSRC = [builddir + '/' + s for s in HDDSROOTHSRC]
HDDSMD5SRC   = [builddir + '/' + s for s in HDDSMD5SRC  ]
FINDALLSRC   = [builddir + '/' + s for s in FINDALLSRC  ]
COMMONBSRC   = [builddir + '/' + s for s in COMMONSRC   ]

# Make programs
hdds_geant  = env.Program(target='%s/hdds-geant'  % builddir, source=HDDSGEANTSRC )
hdds_rootc  = env.Program(target='%s/hdds-root'   % builddir, source=HDDSROOTSRC  )
hdds_rooth  = env.Program(target='%s/hdds-root_h' % builddir, source=HDDSROOTHSRC )
hdds_md5    = env.Program(target='%s/hdds-md5'    % builddir, source=HDDSMD5SRC   )
findall     = env.Program(target='%s/findall'     % builddir, source=FINDALLSRC   )

# ---- Create builders to generate source using hdds programs ---
if SHOWBUILD==0:
	hddsgeantaction = SCons.Script.Action("%s/hdds-geant  $SOURCE > $TARGET" % (builddir), 'HDDS-GEANT [$SOURCE -> $TARGET]')
	hddsrootaction  = SCons.Script.Action("%s/hdds-root   $SOURCE > $TARGET" % (builddir), 'HDDS-ROOTC [$SOURCE -> $TARGET]')
	hddsroothaction = SCons.Script.Action("%s/hdds-root_h $SOURCE > $TARGET" % (builddir), 'HDDS-ROOTH [$SOURCE -> $TARGET]')
	if hasGDMLsupport:
		hddsgdmlaction  = SCons.Script.Action('%s/bin/root -b -q $SOURCE "mkGDML.C(\\"$TARGET\\")" > /dev/null 2>&1' % (rootsys) , 'HDDS-GDML  [$SOURCE -> $TARGET]')
else:
	hddsgeantaction = SCons.Script.Action("%s/hdds-geant  $SOURCE > $TARGET" % (builddir))
	hddsrootaction  = SCons.Script.Action("%s/hdds-root   $SOURCE > $TARGET" % (builddir))
	hddsroothaction = SCons.Script.Action("%s/hdds-root_h $SOURCE > $TARGET" % (builddir))
	if hasGDMLsupport:
		hddsgdmlaction  = SCons.Script.Action('%s/bin/root -b -q $SOURCE "mkGDML.C(\\"$TARGET\\")"' % (rootsys))
hddsgeantbld = SCons.Script.Builder(action = hddsgeantaction )
hddsrootbld  = SCons.Script.Builder(action = hddsrootaction  )
hddsroothbld = SCons.Script.Builder(action = hddsroothaction )
env.Append(BUILDERS = {'HDDSgeant'  : hddsgeantbld })
env.Append(BUILDERS = {'HDDSrootc'  : hddsrootbld  })
env.Append(BUILDERS = {'HDDSrooth'  : hddsroothbld })
if hasGDMLsupport:
	hddsgdmlbld  = SCons.Script.Builder(action = hddsgdmlaction  )
	env.Append(BUILDERS = {'HDDSgdml'   : hddsgdmlbld  })

# --- Use builders to generate source from XML ---
if os.getenv('LD_LIBRARY_PATH'  ) != None : env.AppendENVPath('LD_LIBRARY_PATH'  , '%s/lib' % xerces )  # so libxerces-c.so can be found
if os.getenv('DYLD_LIBRARY_PATH') != None : env.AppendENVPath('DYLD_LIBRARY_PATH', '%s/lib' % xerces )  # so libxerces-c.so can be found
HDDSGEANT3 = env.HDDSgeant(target='%s/hddsGeant3.F' % builddir, source=['main_HDDS.xml']+XMLDEPS)
HDDSROOTC  = env.HDDSrootc(target='%s/hddsroot.C'   % builddir, source=['main_HDDS.xml']+XMLDEPS)
HDDSROOTH  = env.HDDSrooth(target='%s/hddsroot.h'   % builddir, source=['main_HDDS.xml']+XMLDEPS)
CPPROOTC   = env.HDDSrootc(target='%s/cpproot.C'    % builddir, source=['cpp_HDDS.xml','ForwardMWPC_HDDS.xml']+XMLDEPS)
if hasGDMLsupport:
	HDDSGDML   = env.HDDSgdml( target='%s/hddsroot.gdml' % builddir, source='%s/hddsroot.C' % builddir)
	CPPGDML    = env.HDDSgdml( target='%s/cpproot.gdml' % builddir, source='%s/cpproot.C' % builddir)
env.Requires([HDDSGEANT3], hdds_geant)
env.Requires([HDDSROOTC] , hdds_rootc)
env.Requires([HDDSROOTH] , hdds_rooth)
env.Requires([CPPROOTC]  , hdds_rootc)
if hasGDMLsupport:
	env.Requires([HDDSGDML]  , HDDSROOTC  )
	env.Requires([CPPGDML]   , CPPROOTC  )

# --- Build libhddsGeant3.a
libhddsgeant3 = env.Library(target='%s/hddsGeant3' % builddir, source=HDDSGEANT3)
libhdds = env.SharedLibrary(target='%s/hdds' % builddir, source = COMMONBSRC, SHLIBSUFFIX='.so')

# Configure for installation. In principle, we should not need to explicitly
# check if the "install" target was specified. For some unknown reason though,
# scons seems to install things automatically otherwise (Argghh!)
build_targets = map(str,BUILD_TARGETS)
if len(build_targets)>0:
	if 'install' in build_targets:
		env.Install(bin, hdds_geant)
		env.Install(bin, hdds_rootc)
		env.Install(bin, hdds_rooth)
		env.Install(bin, hdds_md5)
		env.Install(bin, findall)

		env.Install('%s/src' % installdir, HDDSGEANT3)
		env.Install('%s/src' % installdir, HDDSROOTC)
		env.Install('%s/src' % installdir, HDDSROOTH)
		env.Install('%s/src' % installdir, CPPROOTC)
		if hasGDMLsupport:
			env.Install('%s/src' % installdir, HDDSGDML)
			env.Install('%s/src' % installdir, CPPGDML)

		env.Install(lib, libhddsgeant3)		
		env.Install(lib, libhdds)		

# Make install target
env.Alias('install', installdir)






