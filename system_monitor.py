#! /usr/bin/env python

from __future__ import print_function
from influxdb import InfluxDBClient

import fabric
from fabric.api import env
from fabric.api import run

from hdd_utils import Drive

import copy
import json
import os
import signal
import subprocess
import sys
import time

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        print("Exiting gracefully")
        self.kill_now = True

def monitor_hdds(machine, drive_paths, period, tags, db):
    killer = GracefulKiller()

    # Parse given tags
    json_acceptable_string = tags.replace("'", "\"")
    tags_set = json.loads(json_acceptable_string)
    tags_set['machine'] = machine

    # Establish connection with InfluxDB
    print("Establishing connection to InfluxDB database... ", end="")
    client = InfluxDBClient(db.addr, db.port, 'root', 'root', db.name)
    print("Done.")

    # Construct drive objects
    drives = [Drive(path, period-10) for path in drive_paths]

    while not killer.kill_now:

        database_dicts = client.get_list_database()
        for remote_db in database_dicts:
            if(remote_db['name'] == db.name):
                break
        else:
            client.create_database(db.name)

        measurement_template = {
            "measurement" : "temperature",
            "tags" : tags_set,
            "fields": {
                "value": None
            }
        }

        measurements = []

        # Take measurements
        for drive in drives:
            temp = drive.temperature(True)
            print(drive.path + ": " + str(temp))
            point = copy.deepcopy(measurement_template)
            point["tags"]["drive"] = drive.path
            point["fields"]["value"] = temp

            print("Adding point: " + str(point))
            measurements.append(point)
            if killer.kill_now:
                print("Breaking mid-measurement")
                return

        print("Sending to InfluxDB:")
        for point in measurements:
            print(str(point))
        print("Write success: ", end="")
        print(client.write_points(measurements))
        print("Measurement complete")
        print("Sleeping for %d seconds..." % period)
        print()
        sys.stdout.flush()

        # Sleep in short bursts, so that we may exit gracefully
        sleep_start = time.time()

        while time.time() - sleep_start < period and not killer.kill_now:
            time.sleep(1)

def get_required_env(name):
    variable = os.environ.get(name)
    if not variable:
        print("Environment variable %s is required. Exiting." % name);
        quit(-1)
    return variable

def main():
    # Required
    machine = get_required_env("MACHINE")
    drives = get_required_env("DRIVES")
    print("Using drives: \"%s\"" % drives)
    drives = drives.split(';')

    # Optional
    machine_addr = os.getenv("MACHINE_ADDRESS", 'localhost')
    machine_port = os.getenv("MACHINE_PORT", 22)
    machine_user = os.getenv("MACHINE_USER", "root")
    db_addr = os.getenv("INFLUXDB_ADDRESS", 'influxdb')
    db_port = os.getenv("INFLUXDB_PORT", 8086)
    db_name = os.getenv("INFLUXDB_NAME", 'hdd_monitor')
    period = int(os.getenv("PERIOD", 120))
    tags = os.getenv("TAGS", "{}")

    class Object():
        pass
    db = Object()
    db.name = db_name
    db.addr = db_addr
    db.port = db_port

    # Setup Fabric environment
    print("Setting Fabric environment...")
    env.user = machine_user
    env.host_string = "%s:%s" % (machine_addr, machine_port)
    env.key_filename = "/ssh/id_rsa.pem"
    fabric.state.output.commands = False
    print("  env.host_string set to: \"" + env.host_string + "\"")

    print("Entering main loop...")
    monitor_hdds(machine, drives, period, tags, db)


if __name__ == "__main__":
    main()

