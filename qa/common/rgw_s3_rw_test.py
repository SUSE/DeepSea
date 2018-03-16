# Script name: rgw_s3_basic_test.py
# REQUIREMENTS: 
# - sudo zypper in -y python-boto
# - Server needs to be ceph admin node and to be able to execute 
# Purpose: 
# - Listing existing buckets 
# - Creating new bucket 
# - Puting a txt based object into newly created bucket 
# - Reading the same object 

import boto.s3.connection
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import sys 
import subprocess
import json 
import string 
import random 

def print_usage():
    MSG = """
    Usage: python s3_rw_test.py RGW_HOST_IP RGW_USER_ID RGW_ZONE 
    RGW_HOST_IP - IP of the rados gateway with port when different than 80 
    RGW_USER_ID - rados gateway user ID; user need to have r/w privileges 

    EXAMPLE: 
    python s3_rw_test.py 192.168.122.152:7080 zone.user
    """
    print(MSG)

def print_bucket_list():
    print("Existing buckets:")
    for bucket in conn.get_all_buckets():
        print "{name}\t{created}".format(name = bucket.name,created = bucket.creation_date)

# RGW hsot IP address 
try: 
    RGW_HOST_IP = sys.argv[1]
except IndexError:
    print_usage()
    sys.exit("Please read usage and try again.")

# getting the TCP port 
try:
    TCP_PORT = int(RGW_HOST_IP.split(':')[1])
    RGW_HOST_IP = RGW_HOST_IP.split(':')[0]
except IndexError: 
    TCP_PORT = 80

# RGW user
try:
    RGW_USER = sys.argv[2]
except IndexError:
    print_usage()
    sys.exit("Please read usage and try again.")

bash_cmd = "radosgw-admin user info --uid=%s --format=json" %RGW_USER
user_info=json.loads(subprocess.check_output(bash_cmd, shell=True))
# user_info.keys()
access_key=user_info['keys'][0]['access_key']
secret_key=user_info['keys'][0]['secret_key']

conn = S3Connection(aws_access_key_id=access_key, aws_secret_access_key=secret_key, host=RGW_HOST_IP, port=TCP_PORT, is_secure=False, calling_format=boto.s3.connection.OrdinaryCallingFormat())

print_bucket_list()

# create new bucket 
rnd_sufix = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
bucket_name = 'bucket_' + rnd_sufix
try:
    bucket = conn.create_bucket(bucket_name)
except S3ResponseError:
    sys.exit("Error: Bucket creation failed.") #TODO get and print python and S3 error code  
else:
    print("Bucket "+bucket_name+" created OK.")

# write object to a bucket 
k = Key(bucket)
k.key = 'test_content'
rnd_data_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(64))
try:
    k.set_contents_from_string('Random chars: ' + rnd_data_string)
except:
    sys.exit("Error: Object putting failed.")

print('Read obj verification OK.') if 'Random chars:' in k.get_contents_as_string() else sys.exit("Error: obj read KO.")

conn.close()

