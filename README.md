# net-snmp-systemd-service-status

This is a snmpd (Net-SNMP) "pass_persist" extension script that generates "is
service up" data for all detected systemd services. On a high level it works as
follows:

1. Uses a private OID subtree ("1.3.9950.1") as a prefix for all OIDs
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

This script has seen multiple iterations which differ a great deal
performance-vise. All tests were conducted on a fairly low power Ubuntu 18.04
or 20.04 VMs:

* Original "pass" script was launched once per OID by snmpd. Querying all units (180) took about 10 seconds. 
* First iteration of "pass_persist" script ran "systemctl is-active" for detected (180) units. Querying all units took about 1.6 seconds.
* Second (current) iteration of "pass_persist" script that gets all the data using one systemctl command. Querying all (62) services took about 0.25 seconds.  
