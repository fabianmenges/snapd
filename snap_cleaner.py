#!/usr/bin/python

import argparse
import datetime
import glob
import sys

from subprocess import call

FIRST_STAGE = 30
SECOND_STAGE = 365

SNAP_PATH = '/home/.snapshots'
SNAP_FORMAT = '%Y-%m-%d-%H-%M'


parser = argparse.ArgumentParser(description='''Removes btrfs subvolumes/snapshots according to the following logic:
                                   1: Keep one snapshot per month for snapshots that are older than %s days
                                   2: Keep one snapshot per week for snapshots that are older than %s days''' % (SECOND_STAGE, FIRST_STAGE))

parser.add_argument('--snapshot-path', dest='snap_path', type=str, default=SNAP_PATH,
                    help='Path with the btrfs snapshots/subvolumes.')
parser.add_argument('--snapshot-name-format', dest='snap_format', type=str, default=SNAP_FORMAT,
                    help='Name format of the snapshot/subvolumes.')
parser.add_argument('--dry-run', action='store_true')


args = parser.parse_args()

def put_in_bucket(bucket, snapshot_name, first, second):
    if first not in bucket:
        bucket[first] = {}
    if second not in bucket[first]:
        bucket[first][second]=[]
    bucket[first][second].append(snapshot_name)
    return bucket


def get_to_delete(snapshots):
    to_delete = []
    for year, bucket in snapshots.items():
        for values in bucket.values():
            values.sort()
            values.pop()
            to_delete.extend(values)
    return to_delete


def delete_snapshots(snapshots, dry):
    for s in snapshots:
        print "Deleting snapshot %s" % s 
        if dry:
            print "Noop"
        else:
            call(['/bin/btrfs', 'subvolume', 'delete', s])
        
        
def main(args):
    
    monthly_buckets = {}
    weekly_buckets = {}

    now = datetime.datetime.now()
  
    filenames = sorted(glob.glob(args.snap_path + '/*'))
    for filename in filenames:
        snapshot_time = None
        try:
            snapshot_time = datetime.datetime.strptime(filename.split('/')[-1], args.snap_format)
        except:
            continue
        else:
            delta = now - snapshot_time
            if delta.days > SECOND_STAGE:
                monthly_buckets = put_in_bucket(monthly_buckets, filename, snapshot_time.year, snapshot_time.month)
            elif delta.days > FIRST_STAGE:
                weekly_buckets = put_in_bucket(weekly_buckets, filename, snapshot_time.year, snapshot_time.isocalendar()[1])
                
    delete_snapshots(get_to_delete(monthly_buckets))
    delete_snapshots(get_to_delete(weekly_buckets))
    
if __name__ == "__main__":
    main(args)
