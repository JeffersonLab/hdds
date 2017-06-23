#!/usr/bin/env perl
open(MAIN,"main_HDDS.xml");
open(FLAT,"> main_flat_HDDS.xml");
while ($line = <MAIN>) {
    if ($line =~ /<!ENTITY /) {
	#print "found a hash entry\n";
	#print $line;
	@t = split(/\s+/, $line);
	#print $t[1],"\n";
	$key = $t[2];
	$xmlfile_raw = $t[4];
	@t1 = split(/"/, $xmlfile_raw);
	$xmlfile = $t1[1];
	#print "$key $xmlfile\n";
	$include_hash{$key} = $xmlfile;
	print FLAT $line;
    } elsif ($line =~ /&/) {
	#print "found an include\n";
	#print $line;
	@t2 = split(/&/, $line);
	@t3 = split(/;/, $t2[1]);
	$entity = $t3[0];
	chomp $entity;
	$xmlfile_include = $include_hash{$entity};
	print "including $xmlfile_include\n";
	open(INCLUDE, $xmlfile_include);
	while ($line_include = <INCLUDE>) {
	    print FLAT $line_include;
	}
    } else {
	print FLAT $line;
    }
}
close(MAIN);
close(FLAT);
exit;
