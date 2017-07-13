#!/bin/bash
# short script to monitor rbd du output via the prometheus text_exporter
# mechanism
# data points exported for every image in all accessable clusters are
# ceph_rbd_image_bytes_provisioned
# ceph_rbd_image_bytes_used

awk_cmd='
{
print "# HELP ceph_rbd_image_bytes_used Used space of an rbd image"
print "# TYPE ceph_rbd_image_bytes_used gauge"
print "ceph_rbd_image_bytes_used{image=\""$1"\",cluster=\""cluster"\"} " $3 * 1024
print "# HELP ceph_rbd_image_bytes_provisioned Provisioned space of an rbd image"
print "# TYPE ceph_rbd_image_bytes_provisioned gauge"
print "ceph_rbd_image_bytes_provisioned{image=\""$1"\",cluster=\""cluster"\"} " $2 * 1024
}'

for conf in /etc/ceph/*.conf
do
    filename=$(basename "$conf")
    cluster="${filename%.*}"
    rbd -c $conf du | sed 1d | awk -v cluster=$cluster "$awk_cmd"
done
