
			Build Notes for HDDS Tools
	    		    Richard Jones
	    		  September 10, 2003
                     last updated July 23, 2015

This document is intended as a quick-start guide for building and using
the hdds tools.  For more information and for discussion of features and
bugs, please go to http://portal.gluex.org and select "forums".

1) Since you are reading this, you have already done the first step.
   From within your hdds work directory you typed:

   halld> cvs checkout hdds
    or
   halld> git clone https://github.com/JeffersonLab/hdds.git
   
2) Download the xerces-c xml library from xml.apache.org and unpack
   it somewhere on your system or GlueX working area.  Getting the sources
   and doing the build yourself (next step) makes sure that you have a
   working installation for your configuration.

3) Build the xerces xml library for your system.

   This is pretty simple.  The instructions are found on the xml.apache.org
   web site.  There are just three steps: define XERCESCROOT to point to the
   base directory where you unpacked xerces-c, then runConfigure and gmake.
   The result is a shared library in the directory xerces-c/lib.

4) Somewhere, perferrably at the top of your GlueX work directory you
   should make a script called setup that sets up some environment
   variables that are needed to locate the XML libraries on your system.
   What that looks like depends on your shell, but for tcsh it looks like:

   halld> cat setup
   setenv HDDS_HOME <your local source directory path>
   setenv XERCESCROOT <your Xerces-C installation path>
   setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/${XERCESCROOT/lib

   For the bash or ksh shells you should use the export command instead of
   setenv.  You will need to source this file before every session, (or
   invoke it with the . operator for ksh or bash).

6) Now if everything was installed correctly, you can build the hdds tools
   by going to the hdds directory you created in step 1 and doing make.

   halld> cd $HDDS_HOME
   halld> scons install

7) For information about the design and use of the hddm tools, see the
   documentation in index.html.
