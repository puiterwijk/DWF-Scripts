#!/bin/env python
# Copyright (c) 2016, Patrick Uiterwijk <patrick@puiterwijk.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import csv
import os
import glob
import sys

# These will never be reported as error: these were merged
# in violation of the assigned blocks.
EXCEPTIONS = ['DWF-2016-89001']


# We do this global
found_error = False
seen_ids = []

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


def test_assigner(assigner, valid_assigners):
    if assigner in valid_assigners:
        # If we're in the valid assigners directly, we're done
        return True
    for valid in valid_assigner:
        if valid.startswith('@') and assigner.endswith(valid):
            # This was an authorized assigner domain (@example.com)
            return True
    return False


def test_line(registry, line):
    global found_error
    global seen_ids

    dwfid = line['DWF_ID']

    # Some syntax checks on DWF IDs
    if dwfid in seen_ids:
        print 'ID duplicate: %s' % dwfid
        found_error = True
    seen_ids.append(dwfid)

    split_id = dwfid.split('-')
    if len(split_id) != 3:
        print 'ID invalid: %s' % dwfid
        found_error = True
        return

    if split_id[0] not in ['DWF']:
        print 'ID not DWF: %s' % dwfid
        found_error = True
        return

    if len(split_id[2]) < 4:
        print 'ID not N4+: %s' % dwfid
        found_error = True
        return

    try:
        int(split_id[1])
    except:
        print 'ID field 1 not numeric: %s' % dwfid
        found_error = True
        return

    try:
        int(split_id[2])
    except:
        print 'ID field 2 not numeric: %s' % dwfid
        found_error = True
        return

    # Check assigner
    if not dwfid in EXCEPTIONS:
        dna = search_dna(registry, split_id[2])
        if not dna:
            print 'Could not find assigner for %s' % dwfid
            found_error = True
            return
        valid_assigners = dna['Valid Assigners']
        if not test_assigner(line['ASSIGNER'], valid_assigners):
            print '%s has incorrect assigner! Should be one of %s, is %s' % \
                (dwfid, valid_assigners, line['ASSIGNER'])
            found_error = True
            return


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

    if found_error:
        print 'Errors were found and reported above'
        sys.exit(2)


if __name__ == '__main__':
    main()
