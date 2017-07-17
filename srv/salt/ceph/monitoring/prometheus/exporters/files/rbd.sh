#!/bin/bash
# short script to monitor rbd du output via the prometheus text_exporter
# mechanism
# data points exported for every image in all accessable clusters are
# ceph_rbd_image_bytes_provisioned
# ceph_rbd_image_bytes_used

awk_cmd='
{
print "ceph_rbd_image_bytes_used{image=\""$1"\",cluster=\""cluster"\"} " $3
print "ceph_rbd_image_bytes_provisioned{image=\""$1"\",cluster=\""cluster"\"} " $2
}'

echo '# HELP ceph_rbd_image_bytes_used Used space of an rbd image
# TYPE ceph_rbd_image_bytes_used gauge
# HELP ceph_rbd_image_bytes_provisioned Provisioned space of an rbd image
# TYPE ceph_rbd_image_bytes_provisioned gauge'

for conf in /etc/ceph/*.conf
do
    filename=$(basename "$conf")
    cluster="${filename%.*}"
    rbd --format json -c $conf du |
    jq ".images[] | [.name, .provisioned_size, .used_size] | @csv" |
    sed -e 's/^"//' -e 's/"$//' -e 's/\\"//g' | # stripe some quotes
    awk -F , -v cluster=$cluster "$awk_cmd"
done
