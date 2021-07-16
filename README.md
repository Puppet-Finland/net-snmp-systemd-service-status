# net-snmp-systemd-service-status

This is a snmpd (Net-SNMP) "pass" extension script that generates "is service
up" data for all detected systemd services. On a high level it works as follows:

1. Use a private OID subtree as a prefix for all OIDs
1. List systemd service unit files on the system
1. Filter out services that can have multiple instances ("@.service")
1. Get status ("is-active") for each unit
1. Convert the name of the service into a valid OID by changing every character into its equivalent decimal ASCII code
1. Sort the OIDs (to prevent snmpwalk from choking on unordered OIDs)
1. Write the sorted OID data (oid, "integer", return value) to a cache file
1. Write the current index to a index file

Cache and index files are necessary because snmpd launches the script once per
get and getnext request and the script's state is lost in between incantations.

When a "get" request is sent print the data in the cache file that
matches the requested OID.

When a "getnext" request is sent print the data on the current line, then
increment the index by one.

The cache file is not updated on every incantation. Instead, it has a lifetime
after which it will be refreshed. This has little practical effect except when
testing the script manually, as you want the latest status anyways in real-life
scenarios.

This script can be used interactively as well. Run it without any parameters to see command-line help.

# Performance

The performance of this script is as good as it can be when doing a simple
snmpget. When doing an snmpwalk it is a lot slower because snmpd launches the
script on every getnext request. In practice walking through ~180 systemd
services takes <10 seconds on a low-end virtual machine.

To boost performance this script would have to rewritten to work as
pass-persist script which snmpd would only launch once. Alternatively there
would have to be a filter to target only the systemd services you're really
interested in.
