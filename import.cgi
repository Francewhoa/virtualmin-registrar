#!/usr/local/bin/perl
# Try to associate a domain registration with this server
use strict;
no strict 'refs';
use warnings;
our (%access, %text, %in);
our $module_name;

require './virtualmin-registrar-lib.pl';
&ReadParse();
&error_setup($text{'import_err'});
$access{'registrar'} || &error($text{'import_ecannot'});

# Get the Virtualmin domain and account
my $d = &virtual_server::get_domain_by("dom", $in{'dom'});
$d || &error(&text('contact_edom', $in{'dom'}));
$d->{$module_name} && &error($text{'import_ealready'});
my ($account) = grep { $_->{'id'} eq $in{'account'} }
		  &list_registrar_accounts();
$account || &error(&text('contact_eaccount', $in{'dom'}));
my $oldd = { %$d };

# Show import progress
&ui_print_unbuffered_header(&virtual_server::domain_in($d),
			    $text{'import_title'}, "");

print &text('import_doing', "<tt>$d->{'dom'}</tt>",
			    "<i>$account->{'desc'}</i>"),"<br>\n";
my $ifunc = "type_".$account->{'registrar'}."_owned_domain";
my ($ok, $msg) = &$ifunc($account, $d->{'dom'},
		      $in{'id_def'} ? undef : $in{'id'});
if (!$ok) {
	print &text('import_failed', $msg),"<p>\n";
	}
elsif (!$msg) {
	print $text{'import_missing'},"<p>\n";
	}
else {
	print &text('import_done', $msg),"<p>\n";

	# Update the domain
	$d->{$module_name} = 1;
	$d->{'registrar_account'} = $account->{'id'};
	$d->{'registrar_id'} = $msg;
	&virtual_server::save_domain($d);

	# Set nameservers to match this system
	if ($in{'ns'}) {
		print $text{'import_nsing'},"<br>\n";
		my $nfunc = "type_".$account->{'registrar'}."_set_nameservers";
		my $err = &$nfunc($account, $d);
		if ($err) {
			print &text('import_failed', $err),"<p>\n";
			}
		else {
			no warnings "once";
			print $virtual_server::text{'setup_done'},"<p>\n";
			use warnings "once";
			}
		}

	# Update the Webmin user
	&virtual_server::refresh_webmin_user($d);
	&virtual_server::run_post_actions();

	# Call any theme post command
	if (defined(&theme_post_save_domain)) {
		&theme_post_save_domain($d, 'modify');
		}
	}

&ui_print_footer(&virtual_server::domain_footer_link($d));
