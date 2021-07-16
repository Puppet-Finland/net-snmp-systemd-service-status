#!/usr/bin/env python3
import linecache
import os
import re
import subprocess
import sys
import time

class SystemdServiceStatus:

    def __init__(self, oid_prefix, cache_file, cache_lifetime, index_file):
        self.cache_file = cache_file
        self.cache_lifetime = cache_lifetime
        self.index_file = index_file
        self.cache = None
        self.oid_prefix = oid_prefix

        # Get the latest index. This is required for getnext().
        self.index = 1
        try:
            with open(index_file, "r") as f:
                self.index = int(f.readline().rstrip())
        except FileNotFoundError:
            pass

        # Cache service status to a file
        self.cache_service_status()

    def cache_service_status(self):
        """Create or refresh service status cache if needed"""

        if os.path.exists(self.cache_file):
            if float(time.time()) - os.path.getmtime(self.cache_file) > self.cache_lifetime and self.index == 1:
                os.remove(self.cache_file)
            else:
                return

        lines = subprocess.check_output(["/bin/systemctl", "list-unit-files", "-t", "service", "--no-legend"]).decode("UTF-8").split("\n")
 
        oids = []
        data = {}

        for line in lines:
            if line and not "@." in line:
               service_name = re.sub(r'\.service\s+\w+$', '', line) 
               service_oid = self.create_oid(service_name)
               try:
                   service_status = subprocess.check_call(["/bin/systemctl", "is-active", service_name], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
               except subprocess.CalledProcessError as cpe:
                   service_status = cpe.returncode

               data[service_oid] = ('integer', service_status, service_name)
               oids.append(service_oid)

        # Sort the oids array. Lovingly borrowed from here:
        #
        # https://rosettacode.org/wiki/Sort_a_list_of_object_identifiers#Python
        #
        # The array sorted array is then used to write the data to the file
        # in correct order.
        oids = sorted(oids, key=lambda x: list(map(int, x.split('.'))))
        self.write_cache(data, oids)

    def write_cache(self, data, oids):
        """Write sorted cache to disk"""
        cache = open(self.cache_file, "a+")
        for oid in oids:
            output = ".%s %s %s %s\n" % (oid, data[oid][0], data[oid][1], data[oid][2])
            cache.write(output)

    def get(self, oid):
        """Print OID, data type and service status return code for OID"""
        self.cache = open(self.cache_file, "r")

        for line in self.cache.readlines():
            data = line.split(" ")
            if data[0] == oid:
                self.print_data(data)

    def getnext(self):
        """Get the next OID from the cache"""
        data = linecache.getline(self.cache_file, self.index).split(" ")
        if data == ['']:
            self.index = 1
            self.update_index()
            sys.exit(0)
        else:
            self.print_data(data)
            self.index += 1
            self.update_index()

    def update_index(self):
        """Update the index file"""
        with open(self.index_file, "w+") as f:
            f.write(str(self.index))

    def print_data(self, data):
        """Print data in the format snmpd wants it"""
        print(data[0])
        print(data[1])
        print(data[2])

    def create_oid(self, name):
        """Generate oid programmatically from the service name"""
        oid = self.oid_prefix

        for char in name:
            oid += "."
            oid += str(ord(char))

        return oid.lstrip(".")

def main():
    oid_prefix = "1.3.9950.1"
    cache_file = "/var/lib/snmp/systemd-service-status.cache"
    index_file = "/var/lib/snmp/systemd-service-status.index"
    cache_lifetime = 240

    try:
        op = sys.argv[1]
        oid = sys.argv[2]
    except IndexError:
        print("Usage: systemd-service-status.py [-g|-n] [OID]")
        sys.exit(1)

    s = SystemdServiceStatus(oid_prefix, cache_file, cache_lifetime, index_file)

    if op == "-g":
        s.get(oid)
    elif op == "-n":
        s.getnext()
    else:
        print("ERROR: unknown operation %s" % (op))

if __name__ == "__main__":
    main()
