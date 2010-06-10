#!/usr/bin/env perl

use HTML::WikiConverter;
use DBI;

$| = 1;

$conv = new HTML::WikiConverter(dialect=>'Markdown', link_style=>'inline');
if (!$ARGV[0]) {
    print "Usage: 2_convert_to_markdown.pl <dsn>\n";
    exit(1);
}
$dbh = DBI->connect("dbi:Pg:" . $ARGV[0], '', '', { AutoCommit=> 0});

#print "Converting news...\n";
#News();
print "Converting events..\n";
Events();
print "Converting quotes...\n";
Quotes(); #NOTE! Quotes need manual cleanup! (more than the others, but they all do, really)

sub News() {
	$dbh->do("TRUNCATE TABLE news_newsarticle");
	$r = $dbh->selectall_arrayref("SELECT id,posted,posted_by,headline,summary,story FROM oldweb.news INNER JOIN oldweb.news_text ON news.id=news_text.newsid AND news_text.language='en' WHERE approved ORDER BY id");
	$ins = $dbh->prepare("INSERT INTO news_newsarticle (id, org_id, approved, date, title, content) VALUES (?, 0, 't', ?, ?, ?)");
	print "Done loading, now starting conversion...\n";
	$last = -10;$now = 0;
	for my $row (@$r) {
	    $now++;
	    if ($now - $last > 2) {
		print "$now / " . scalar(@$r) . "\r";
		$last = $now;
	    }
	     
	   $ins->execute($row->[0],
	   		 $row->[1],
	   		 $row->[3],
	   		 ConvertHtmlToMarkdown($row->[5])
	       ) || die "Failed to insert!\n";
	}
	$dbh->do("SELECT setval('news_newsarticle_id_seq', max(id)+1) FROM news_newsarticle") || die "Failed to setval";
	$dbh->commit();
	print "Done.\n";
}

sub Events {
    $dbh->do("TRUNCATE TABLE events_event") || die "Failed to truncate\n";
	$r = $dbh->selectall_arrayref("SELECT id,posted,posted_by,start_date,end_date,training,COALESCE(organisation,''),country,state,city,event,COALESCE(summary,''),COALESCE(details,'') FROM oldweb.events INNER JOIN oldweb.events_text ON events.id=events_text.eventid AND events_text.language='en' INNER JOIN oldweb.events_location ON events.id=events_location.eventid WHERE approved ORDER BY id");
	$ins = $dbh->prepare("INSERT INTO events_event (id,approved,org_id,title,city,state,country_id,training,startdate,enddate,summary,details) VALUES (?,'t',(SELECT id FROM core_organisation WHERE name=?),?,?,?,?,?,?,?,?,?)");
	$last = -10;$now = 0;
	for my $row (@$r) {
	    $now++;
	    if ($now - $last > 2) {
		print "$now / " . scalar(@$r) . "\r";
		$last = $now;
	    }
		$ins->execute($row->[0],
				$row->[6],
				$row->[10],
				$row->[9],
				$row->[8],
				$row->[7],
				$row->[5],
				$row->[3],
				$row->[4],
				ConvertHtmlToMarkdown($row->[11]),
				ConvertHtmlToMarkdown($row->[12])
		    ) || die "Failed to insert\n";
	}
    $dbh->do("SELECT setval('events_event_id_seq', max(id)+1) FROM events_event") || die "Failed to setval\n";
	$dbh->commit();
}

sub Quotes {
    $dbh->do("TRUNCATE TABLE quotes_quote") || die "Failed to truncate\n";
    $r = $dbh->selectall_arrayref("SELECT quoteid,quote,tagline FROM oldweb.quotes_text WHERE language='en' ORDER BY 1");
	$ins = $dbh->prepare("INSERT INTO quotes_quote(id,approved,quote,who,org,link) VALUES (?,'t',?,?,?,?)");
	$last = -10;$now = 0;
	for my $row (@$r) {
	    $now++;
	    if ($now - $last > 2) {
		print "$now / " . scalar(@$r) . "\r";
		$last = $now;
	    }
		$tag = $row->[2];
		if ($tag =~ /^([^<]+), <a href="([^"]+)">([^<]+)<\/a>(.*)$/) {
			print "match $tag\n";
		   $who = $1;
		   $link = $2;
		   $org = $3 . $4;
		}
		elsif ($tag =~ /^([^,]+), (.*)$/s) {
		   $who = $1;
		   $org = $2;
		   $link = '';
		}
		elsif ($tag =~ /^<a href="([^"]+)">([^<]+)<\/a>(.*)$/) {
		   $who = '';
		   $link = $1;
		   $org = $3 . $4;
		}
		else {
		   die "Could not parse $tag\n";
		}
	    $ins->execute($row->[0], $row->[1], $who, $org, $link) || die "Failed to insert\n";
	}
    $dbh->do("SELECT setval('quotes_quote_id_seq', max(id)+1) FROM quotes_quote") || die "Failed to setval\n";
	$dbh->commit();
}

sub ConvertHtmlToMarkdown {
	$html = shift;
	# Blank?
	return "" if $html =~ /^\s*$/;
	# First apply our website style translation thingy
	$html =~ s/[\r\n]+/<p>\n/g;
#	print "Attempt to convert\n";
#	print $html  ."\n";
#	print "result:\n";
#	print $conv->html2wiki($html);
	
	return $conv->html2wiki($html);
}
