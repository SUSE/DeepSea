# This file is part of the DeepSea integration test suite

#
# separate file to house the pool creation functions
#

function create_pool_incrementally {
    # Special-purpose function for creating pools incrementally. For example,
    # if your test case needs 2 pools "foo" and "bar", but you cannot create
    # them all at once for some reason. Otherwise, use create_all_pools_at_once.
    #
    # sample usage:
    #
    # create_pool foo 2
    # ... do something ...
    # create_pool bar 2
    # ... do something else ...
    #
    local POOLNAME=$1
    test -n "$POOLNAME"
    local TOTALPOOLS=$2
    test -n "$TOTALPOOLS"
    local PGSPERPOOL=$(pgs_per_pool $TOTALPOOLS)
    ceph osd pool create $POOLNAME $PGSPERPOOL $PGSPERPOOL replicated
}

function create_all_pools_at_once {
    # sample usage: create_all_pools_at_once foo bar
    local TOTALPOOLS="${#@}"
    local PGSPERPOOL=$(pgs_per_pool $TOTALPOOLS)
    for POOLNAME in "$@"
    do
        ceph osd pool create $POOLNAME $PGSPERPOOL $PGSPERPOOL replicated
    done
    ceph osd pool ls detail
}

function pre_create_pools {
    # pre-create pools with calculated number of PGs so we don't get health
    # warnings after Stage 4 due to "too few" or "too many" PGs per OSD
    # (the "write_test" pool is used in common/sanity-basic.sh)
    sleep 10
    POOLS="write_test"
    test "$MDS" && POOLS+=" cephfs_data cephfs_metadata"
    test "$IGW" && POOLS+=" iscsi-images"
    test "$OPENSTACK" && POOLS+=" smoketest-cloud-backups smoketest-cloud-volumes smoketest-cloud-images smoketest-cloud-vms"
    create_all_pools_at_once $POOLS
    ceph osd pool application enable write_test deepsea_qa
    test "$IGW" && ceph osd pool application enable iscsi-images rbd
    sleep 10
}
