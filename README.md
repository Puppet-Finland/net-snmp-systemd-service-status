# net-snmp-systemd-service-status

This is a snmpd (Net-SNMP) "pass_persist" extension script that generates "is
service up" data for all detected systemd services. On a high level it works as
follows:

1. Uses a private OID subtree as a prefix for all OIDs
1. Lists systemd service unit files on the system
1. Filters out services that can have multiple instances ("@.service")
1. Gets the numeric return value of systemctl is-active for each service
1. Convert the name of the service into a valid OID by changing every character into its equivalent decimal ASCII code
1. Store all data (oid, data type, value, service name) in a dictionary
1. Create a sorted list of oids used for snmpwalk / getnext
1. Provide snmpd the data it requests by listening on standard input and answering queries as documented in snmpd.conf

This script can be used interactively as well. No parameters are needed, just
talk to the script like described in snmpd.conf.

# Performance

This script was originally a "pass" script, which meant that snmpd would launch
the script once per "getnext" request. On a relatively low-powered Ubuntu 18.04
VM with 180 systemd service  getting systemd service status took about 10
seconds. With the current pass_persist approach querying only takes about 1.6
seconds.
