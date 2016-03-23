#!/bin/env python
# Copyright (c) 2016, Patrick Uiterwijk <patrick@puiterwijk.org>
# All rights reserved.
#
# This file is part of DWF-Scripts.
#
# DWF-Scripts is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DWF-Scripts is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DWF-Scripts.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import csv
import os
import glob
import sys

# These will never be reported as error: these were merged
# in violation of the assigned blocks.
EXCEPTIONS = ['DWF-2016-89001']


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('dwf_database_path',
                        help='Path to a checked out DWF database')
    parser.add_argument('dna_registry_path',
                        help='Path to a checked out DNA Registry')
    parser.add_argument('--year-to-check',
                        default=0,
                        help='Only check a specific DWF database year')

    return parser.parse_args()


def parse_registry(dbpath):
    registry = []
    with open(dbpath, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            registry.append(row)
    return registry


def search_dna(registry, iden):
    iden = int(iden)
    for dna in registry:
        start = int(dna['Block start'].split('-')[2])
        end = int(dna['Block end'].split('-')[2])
        if start <= iden and iden <= end:
            return dna


def test_line(registry, line):
    split_id = line['DWF_ID'].split('-')
    if len(split_id) != 3:
        print 'Line invalid: %s' % line
        sys.exit(2)

    # Check assigner
    if not line['DWF_ID'] in EXCEPTIONS:
        dna = search_dna(registry, split_id[2])
        if not dna:
            print 'Could not find assigner for %s' % line['DWF_ID']
            print line
            sys.exit(2)
        if dna['Email'] != line['ASSIGNER']:
            print '%s has incorrect assigner! Should be %s, is %s' % \
                (line['DWF_ID'], dna['Email'], line['ASSIGNER'])


def test_file(registry, filename):
    with open(filename, 'r') as checkpath:
        reader = csv.DictReader(checkpath, delimiter=',', quotechar='"')
        for row in reader:
            test_line(registry, row)


def main():
    args = parse_args()

    if not os.path.isfile(os.path.join(args.dwf_database_path,
                                       'DWF-Example.csv')):
        print 'Please check the DWF Database argument'
        sys.exit(1)
    regpath = os.path.join(args.dna_registry_path, 'DNA-Registry.csv')
    if not os.path.isfile(regpath):
        print 'Please check the DNA Registry argument'
        sys.exit(1)

    if args.year_to_check != 0 and not os.path.isfile(os.path.join(
            args.dwf_database_path, 'DWF-Database-%s.csv' % args.year_to_check)):
        print 'Please check year to check argument'
        sys.exit(1)

    registry = parse_registry(regpath)

    if args.year_to_check != 0:
        filename = os.path.join(args.dwf_database_path, 'DWF-Database-%s.csv' % args.year_to_check)
        test_file(registry, filename)
    else:
        for filename in glob.glob('%s/DWF-Database-*.csv' % args.dwf_database_path):
            test_file(registry, filename)


if __name__ == '__main__':
    main()
