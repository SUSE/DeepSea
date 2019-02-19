#!/bin/bash
# short script to monitor rbd du output via the prometheus text_exporter
# mechanism
# data points exported for every image in all accessable clusters are
# ceph_rbd_image_bytes_provisioned
# ceph_rbd_image_bytes_used
me=`basename "$0"`

function clean_up {
    rm -rf /var/lock/$me.lock
}

if mkdir /var/lock/$me.lock; then
    (>&2 echo "$me lock succeeded")
    trap clean_up EXIT SIGINT SIGTERM
else
    (>&2 echo "$me couldn't take lock...giving up")
    exit 1
fi

awk_cmd='
{
    ($4!="")? snap=sprintf(",snapshot=\"%s\"", $4) : snap=""

    printf "ceph_rbd_image_bytes_used{image=\"%s\"%s,cluster=\""cluster"\",pool=\""pool"\"} %s\n", $1, snap, $3;
    printf "ceph_rbd_image_bytes_provisioned{image=\"%s\"%s,cluster=\""cluster"\",pool=\""pool"\"} %s\n", $1, snap, $2;
}'

echo '# HELP ceph_rbd_image_bytes_used Used space of an rbd image
# TYPE ceph_rbd_image_bytes_used gauge
# HELP ceph_rbd_image_bytes_provisioned Provisioned space of an rbd image
# TYPE ceph_rbd_image_bytes_provisioned gauge'

# iterate over ceph.conf's in case multiple clusters are accessable
for conf in /etc/ceph/*.conf
do
    filename=$(basename "$conf")
    cluster="${filename%.*}"
    pools="$(ceph -c $conf osd lspools 2>/dev/null | sed 's/[[:digit:]]\+ \([^,]*\),/\1 /g')"
    for pool in $pools
    do
        for img in `rbd -p $pool ls`; do
            if rbd -p $pool info $img | grep -q "features:.*fast-diff.*"; then
                rbd -p $pool --format json -c $conf du $img 2>/dev/null |
                jq ".images[] | [.name, .provisioned_size, .used_size, .snapshot] | @csv" |
                sed -e 's/^"//' -e 's/"$//' -e 's/\\"//g' | # stripe some quotes
                awk -F , -v cluster=$cluster -v pool=$pool "$awk_cmd"
            fi
        done
    done
done
