#!/usr/bin/env python

import os
import argparse
import json
import requests
import sqlite3


def options():
    """
    Parse command-line options.

    Inputs:

    Returns:

    Raises:

    :return args:
    """
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Collect traffic statistics for a GitHub repository.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", help="JSON configuration file.", required=True)
    # Process the arguments
    args = parser.parse_args()

    # Does the configration file exist?
    if not os.path.exists(args.config):
        raise IOError("Configuration file {0} does not exist!".format(args.config))

    # Read the configuration file
    config_file = open(args.config, "r")
    # Load the JSON configuration data
    config = json.load(config_file)
    config_file.close()

    # Open the database (or create it if it does not exist)
    args.connect = sqlite3.connect(config["db"])
    args.connect.row_factory = dict_factory
    args.connect.text_factory = str
    args.db = args.connect.cursor()

    # Initialize the database tables if they do not exist
    # Create a table to store clone statistics.
    #     timestamp = UTC date and time when statistics were gathered
    #     count = Total number of clones for the timestamp date
    #     unique = Total unique clones for the timestamp date
    args.db.execute("CREATE TABLE IF NOT EXISTS `clones` (`timestamp` TEXT PRIMARY KEY, `count` INTEGER, "
                    "`unique` INTEGER);")
    # Create a table to store view statistics.
    #     timestamp = UTC date and time when statistics were gathered
    #     count = Total number of views for the timestamp date
    #     unique = Total unique views for the timestamp date
    args.db.execute("CREATE TABLE IF NOT EXISTS `views` (`timestamp` TEXT PRIMARY KEY, `count` INTEGER, "
                    "`unique` INTEGER);")

    # Store the GitHub repository and access_token in args
    args.repo = config["repo"]
    args.token = config["access_token"]

    return args


def dict_factory(cursor, row):
    """
    Replace the row_factory result constructor with a dictionary constructor.

    Inputs:
           cursor: (object) the sqlite3 database cursor object.
           row: (list) a result list.
    Returns:
           d: (dictionary) sqlite3 results dictionary.
    Raises:

    :param cursor: object
    :param row: list
    :return d: dict
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def main():
    # Parse user input
    args = options()

    # Get GitHub repo clone statistics
    response = requests.get("https://api.github.com/repos/{0}/traffic/clones?access_token={1}".format(args.repo,
                                                                                                      args.token))
    if response.status_code != 200:
        raise IOError("GitHub API call failed. Status code: {0}, Reason: {1}.".format(response.status_code,
                                                                                      response.reason))
    clones = response.json()

    # Add clone data to the database
    # Each clone_stat is statistics for a single day
    for clone_stat in clones["clones"]:
        # Query the database with the given timestamp to see if data for this day has already been logged
        results = args.db.execute("SELECT `timestamp` FROM `clones` WHERE `timestamp` = ?", [clone_stat["timestamp"]])
        result = results.fetchone()
        # If data for this day is not in the database, add it to the clones table
        if result is None:
            args.db.execute("INSERT INTO `clones` VALUES (?, ?, ?)", (clone_stat["timestamp"], clone_stat["count"],
                                                                      clone_stat["uniques"]))
    # Get GitHub repo view statistics
    response = requests.get("https://api.github.com/repos/{0}/traffic/views?access_token={1}".format(args.repo,
                                                                                                     args.token))
    if response.status_code != 200:
        raise IOError("GitHub API call failed. Status code: {0}, Reason: {1}.".format(response.status_code,
                                                                                      response.reason))
    views = response.json()

    # Add view data to the database
    # Each view_stat is statistics for a single day
    for view_stat in views["views"]:
        # Query the database with the given timestamp to see if data for this day has already been logged
        results = args.db.execute("SELECT `timestamp` FROM `views` WHERE `timestamp` = ?", [view_stat["timestamp"]])
        result = results.fetchone()
        # If data for this day is not in the database, add it to the views table
        if result is None:
            args.db.execute("INSERT INTO `views` VALUES (?, ?, ?)", (view_stat["timestamp"], view_stat["count"],
                                                                     view_stat["uniques"]))
    # Save the data and close the database connection
    args.connect.commit()
    args.db.close()
    args.connect.close()


if __name__ == '__main__':
    main()
