
import os
import sys
import subprocess
import glob
import SCons


# Get command-line options
SHOWBUILD = ARGUMENTS.get('SHOWBUILD', 0)

# Get platform-specific name
osname = os.getenv('BMS_OSNAME', 'build')

# Setup initial environment
builddir   = ".%s" % (osname)
installdir = "#%s" %(osname)
include    = "%s/include" % (installdir)
bin        = "%s/bin" % (installdir)
lib        = "%s/lib" % (installdir)
env = Environment(CXX         = os.getenv('CXX', 'g++'),
                  CC          = os.getenv('CC' , 'gcc'),
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
else:
	hddsgeantaction = SCons.Script.Action("%s/hdds-geant  $SOURCE > $TARGET" % (builddir))
	hddsrootaction  = SCons.Script.Action("%s/hdds-root   $SOURCE > $TARGET" % (builddir))
	hddsroothaction = SCons.Script.Action("%s/hdds-root_h $SOURCE > $TARGET" % (builddir))
hddsgeantbld = SCons.Script.Builder(action = hddsgeantaction )
hddsrootbld  = SCons.Script.Builder(action = hddsrootaction  )
hddsroothbld = SCons.Script.Builder(action = hddsroothaction )
env.Append(BUILDERS = {'HDDSgeant'  : hddsgeantbld })
env.Append(BUILDERS = {'HDDSrootc'  : hddsrootbld  })
env.Append(BUILDERS = {'HDDSrooth'  : hddsroothbld })

# --- Use builders to generate source from XML ---
if os.getenv('LD_LIBRARY_PATH'  ) != None : env.AppendENVPath('LD_LIBRARY_PATH'  , '%s/lib' % xerces )  # so libxerces-c.so can be found
if os.getenv('DYLD_LIBRARY_PATH') != None : env.AppendENVPath('DYLD_LIBRARY_PATH', '%s/lib' % xerces )  # so libxerces-c.so can be found
HDDSGEANT3 = env.HDDSgeant(target='%s/hddsGeant3.F' % builddir, source='main_HDDS.xml')
HDDSROOTC  = env.HDDSrootc(target='%s/hddsroot.C'   % builddir, source='main_HDDS.xml')
HDDSROOTH  = env.HDDSrooth(target='%s/hddsroot.h'   % builddir, source='main_HDDS.xml')
env.Requires([HDDSGEANT3], hdds_geant)
env.Requires([HDDSROOTC] , hdds_rootc)
env.Requires([HDDSROOTH] , hdds_rooth)

# --- Build libhddsGeant3.a
libhddsgeant3 = env.Library(target='%s/hddsGeant3' % builddir, source=HDDSGEANT3)

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

		env.Install(lib, libhddsgeant3)		

# Make install target
env.Alias('install', installdir)






