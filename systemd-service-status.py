#!/usr/bin/env python3
import logging
import os
import re
import subprocess
import sys
import time

class SystemdServiceStatus:

    def __init__(self, oid_prefix):
        """Object containing information about systemd services and their status"""
        self.oid_prefix = oid_prefix

        # self.data is a dictionary that contains all systemd service data using programmatically
        # generated OID as the key:
        #
        # --- snip ---
        # '1.3.9950.1.115.115.115.100.45.115.101.99.114.101.116.115': ('integer', 3, 'sssd-secrets'),
        # '1.3.9950.1.115.115.115.100': ('integer', 0, 'sssd'),
        # --- snip ---
        self.data = {}

        # self.sorted_oids enables iterating over the OIDs in correct order
        # while having the data in a non-ordered dictionary (self.data).
        self.sorted_oids = []

        # Get systemd service status and store it in self.data. Also populate
        # self.sorted_oids.
        self.cache_service_status()

    def cache_service_status(self):
        """Cache service status"""

        # Temporary data structure used to create sorted oid list later
        oids = [self.oid_prefix]

        lines = subprocess.check_output(["/bin/systemctl", "list-units", "-a", "-t", "service", "--no-legend"]).decode("UTF-8").split("\n")

        for line in lines:
            # Filter out systemd services that are service instance "templates" and
            # not real services, e.g. openvpn@.service.
            if line and not "@." in line:
               # This pattern will get the service name and current status. The test string will be something like
               #
               # accounts-daemon.service            loaded active running Accounts Service
               #
               # Regular expression can be easily tested online, e.g. here: https://pythex.org
               #
               result = re.search(r"^(.+)\.service\s+[\w|-]+\s+\w+\s+(\w+)\s+.*$", line)
               service_name = result.group(1)
               service_status = result.group(2)

               if service_status == 'running':
                   service_status = 0
               else:
                   service_status = 1

               service_oid = self.create_oid(service_name)

               self.data[service_oid] = ('integer', service_status, service_name)
               oids.append(service_oid)

        # Sort the oids array. Lovingly borrowed from here:
        #
        # https://rosettacode.org/wiki/Sort_a_list_of_object_identifiers#Python
        #
        # The array sorted array is then used to output data in the correct order when using
        # getnext (snmpwalk)
        self.sorted_oids = sorted(oids, key=lambda x: list(map(int, x.split('.'))))

    def create_oid(self, name):
        """Generate oid programmatically from the service name"""
        oid = self.oid_prefix

        for char in name:
            oid += "."
            oid += str(ord(char))

        return oid.lstrip(".")

def getline():
    return sys.stdin.readline().strip()

def output(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def main():
    oid_prefix = "1.3.9950.1"

    s = SystemdServiceStatus(oid_prefix)

    # The main loop that talks with snmpd. Mostly taken from
    #
    # https://net-snmp.sourceforge.io/wiki/index.php/Tut:Extending_snmpd_using_shell_scripts#Pass_persist
    try:
        while True:
            command = getline()

            if command == "":
                sys.exit(0)

            # snmpd 5.4.2.1 sends a PING before every snmp command
            elif command == "PING":
                output("PONG")

            elif command == "set":
                oid = getline()
                type_and_value = getline()
                output("not-writable")

            elif command == "get":
                oid = getline()
                output(str(oid))
                output(str(s.data[oid.lstrip(".")][0]))
                output(str(s.data[oid.lstrip(".")][1]))

            elif command == "getnext":
                oid = getline()
                ni = s.sorted_oids.index(oid.lstrip(".")) + 1
                output("." + str(s.sorted_oids[ni]))
                output(str(s.data[s.sorted_oids[ni]][0]))
                output(str(s.data[s.sorted_oids[ni]][1]))

            else:
                pass
                logging.error("Unknown command: %s" % command)

    # If we get an exception, spit it out to the log then quit
    # (by propagating exception).
    # snmpd will restart the script on the next request.
    except Exception as ep:
        f = open("/var/lib/snmp/systemd-service-status.err.log", "a")
        f.write(ep)
        f.close()
        logging.error(e)
        raise

if __name__ == "__main__":
    main()
