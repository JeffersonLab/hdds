ifdef DEBUG
        DEBUG_SUFFIX = _d
	FCOPTS += -g
endif
	OStype = $(shell uname)

	CC = /usr/bin/g++
	COPTS = -g -D_REENTRANT

ifeq ($(OStype),OSF1)
	COPTS = -g -D_REENTRANT -DBASENAME_USE_BUILTIN
endif
ifeq ($(OStype),SunOS)
	CC = CC
        COPTS = -D_REENTRANT -DBASENAME_IN_LIBGEN
endif
ifeq ($(OStype),Darwin)
	CC = g++
        COPTS = -D_REENTRANT -DBASENAME_IN_LIBGEN
endif

ifndef BUILDS
 BUILDS = $(HALLD_HOME)/src/programs/Simulation
endif

BINDIR = bin/$(BMS_OSNAME)
LIBDIR = lib/$(BMS_OSNAME)
OBJDIR = obj$(DEBUG_SUFFIX)/$(BMS_OSNAME)
SRCDIR = src

ifndef NO_COMPILER_MOD
include Makefile.compilers
endif
WHICH_FC := $(shell which $(FC))

XML_SOURCE = BarrelEMcal_HDDS.xml BeamLine_HDDS.xml CentralDC_HDDS.xml\
             CerenkovCntr_HDDS.xml ForwardDC_HDDS.xml ForwardEMcal_HDDS.xml\
             ForwardTOF_HDDS.xml Material_HDDS.xml Solenoid_HDDS.xml \
             StartCntr_HDDS.xml Target_HDDS.xml UpstreamEMveto_HDDS.xml \
	     Regions_HDDS.xml PairSpect_HDDS.xml main_HDDS.xml

all: bms_osname_check fortran_compiler_check make_dirs $(SRCDIR)/hddsroot.C $(SRCDIR)/hddsroot.h $(LIBDIR)/libhddsGeant3$(DEBUG_SUFFIX).a

bms_osname_check:
ifdef BMS_OSNAME
	@echo BMS_OSNAME = $(BMS_OSNAME)
else
	@echo BMS_OSNAME not set; exit 1
endif

fortran_compiler_check:
	@echo FORTRAN compiler = $(FC)
ifeq ($(strip $(WHICH_FC)),)
	@echo Make cannot find FORTRAN compiler.; \
	echo Invoke make with compiler definition, turning off Makefile compiler guessing in command line, e. g.,; \
	echo; \
	echo "    make FC=gfortran NO_COMPILER_MOD=1"; \
	echo; \
	exit 1
endif

make_dirs:
	mkdir -p $(BINDIR) $(LIBDIR) $(OBJDIR) $(SRCDIR)

$(SRCDIR)/hddsMCfast.db: $(BINDIR)/hdds-mcfast $(XML_SOURCE)
	ln -sf $(MCFAST_DIR)/db db
	$(BINDIR)/hdds-mcfast main_HDDS.xml >$@
	rm db

$(SRCDIR)/hddsGeant3.F: $(BINDIR)/hdds-geant $(XML_SOURCE)
	$(BINDIR)/hdds-geant main_HDDS.xml >$@

$(SRCDIR)/hddsroot.C: $(BINDIR)/hdds-root $(XML_SOURCE)
	$(BINDIR)/hdds-root main_HDDS.xml >$@

$(SRCDIR)/hddsroot.h: $(BINDIR)/hdds-root_h $(XML_SOURCE)
	$(BINDIR)/hdds-root_h main_HDDS.xml >$@

$(BINDIR)/hdds-geant: hdds-geant.cpp XParsers.cpp XParsers.hpp \
            XString.cpp XString.hpp hddsCommon.cpp hddsCommon.hpp
	$(CC) $(COPTS) -I$(XERCESCROOT)/include -o $@ $< \
	hddsCommon.cpp XParsers.cpp XString.cpp \
	-L$(XERCESCROOT)/lib -lxerces-c

$(BINDIR)/hdds-root: hdds-root.cpp hdds-root.hpp XParsers.cpp XParsers.hpp \
           XString.cpp XString.hpp hddsCommon.cpp hddsCommon.hpp
	$(CC) $(COPTS) -I$(XERCESCROOT)/include -o $@ $< \
	hddsCommon.cpp XParsers.cpp XString.cpp \
	-L$(XERCESCROOT)/lib -lxerces-c

$(BINDIR)/hdds-root_h: hdds-root_h.cpp hdds-root.hpp XParsers.cpp XParsers.hpp \
           XString.cpp XString.hpp hddsCommon.cpp hddsCommon.hpp
	$(CC) $(COPTS) -I$(XERCESCROOT)/include -o $@ $< \
	hddsCommon.cpp XParsers.cpp XString.cpp \
	-L$(XERCESCROOT)/lib -lxerces-c

$(BINDIR)/hdds-mcfast: hdds-mcfast.cpp XParsers.cpp XParsers.hpp\
             XString.cpp XString.hpp
	$(CC) $(COPTS) -I$(XERCESCROOT)/include -o $@ $< \
	XParsers.cpp XString.cpp -L$(XERCESCROOT)/lib -lxerces-c

$(BINDIR)/findall: findall.cpp XParsers.cpp XParsers.hpp hddsCommon.hpp hddsCommon.cpp \
         XString.cpp XString.hpp hddsBrowser.hpp hddsBrowser.cpp
	$(CC) $(COPTS) -I$(XERCESCROOT)/include -o $@ $< \
	hddsBrowser.cpp hddsCommon.cpp XParsers.cpp XString.cpp \
	-L$(XERCESCROOT)/lib -lxerces-c

$(BINDIR)/xpath-example: xpath-example.cpp
	$(CC) $(COPTS) -I$(XALANCROOT)/include -I$(XERCESCROOT)/include \
	-o $@ xpath-example.cpp \
	-L$(XALANCROOT)/lib -lxalan-c -L$(XERCESCROOT)/lib -lxerces-c

$(OBJDIR)/hddsGeant3.o: $(SRCDIR)/hddsGeant3.F
	$(FC) $(FCOPTS) -c -o $(OBJDIR)/hddsGeant3.o $(SRCDIR)/hddsGeant3.F

$(LIBDIR)/libhddsGeant3$(DEBUG_SUFFIX).a: $(OBJDIR)/hddsGeant3.o
	$(AR) rv $@ $<

clean:
	rm -rfv $(BINDIR) $(SRCDIR) $(OBJDIR) $(LIBDIR)

pristine: clean
