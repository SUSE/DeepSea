# This file is part of the DeepSea integration test suite

#
# functions for generating storage proposals
#

function proposal_populate_dmcrypt {
    salt-run proposal.populate encryption='dmcrypt' name='dmcrypt'
}

function proposal_populate_filestore {
    salt-run proposal.populate format='filestore' name='filestore'
}


#
# functions for generating policy.cfg
#

function policy_cfg_base {
  cat <<EOF > /srv/pillar/ceph/proposals/policy.cfg
# Cluster assignment
cluster-ceph/cluster/*.sls
# Common configuration
config/stack/default/global.yml
config/stack/default/ceph/cluster.yml
# Role assignment - master
role-master/cluster/${SALT_MASTER}*.sls
# Role assignment - admin
role-admin/cluster/*.sls
EOF
}

function policy_cfg_mon_flex {
  local TOTALNODES=$(json_total_nodes)
  test -n "$TOTALNODES"
  if [ "$TOTALNODES" -eq 1 ] ; then
    echo "Only one node in cluster; deploying 1 mon and 1 mgr"
    policy_cfg_one_mon
  elif [ "$TOTALNODES" -eq 2 ] ; then
    echo "2-node cluster; deploying 1 mon and 1 mgr"
    policy_cfg_one_mon
  elif [ "$TOTALNODES" -ge 3 ] ; then
    policy_cfg_three_mons
  else
    echo "Unexpected number of nodes ->$TOTALNODES<-: bailing out!"
    exit 1
  fi
}

function policy_cfg_one_mon {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - 1 mon, 1 mgr
role-mon/cluster/*.sls slice=[:1]
role-mgr/cluster/*.sls slice=[:1]
EOF
}

function policy_cfg_three_mons {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - 3 mons, 3 mgrs
role-mon/cluster/*.sls slice=[:3]
role-mgr/cluster/*.sls slice=[:3]
EOF
}

function policy_cfg_storage {
    test -n "$CLIENT_NODES"
    test -n "$STORAGE_PROFILE"

    if [ "$CLIENT_NODES" -eq 0 ] ; then
        cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-$STORAGE_PROFILE/cluster/*.sls
profile-$STORAGE_PROFILE/stack/default/ceph/minions/*yml
EOF
    elif [ "$CLIENT_NODES" -ge 1 ] ; then
        cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-$STORAGE_PROFILE/cluster/*.sls slice=[:-$CLIENT_NODES]
profile-$STORAGE_PROFILE/stack/default/ceph/minions/*yml slice=[:-$CLIENT_NODES]
EOF
    else
        echo "Unexpected number of client nodes ->$CLIENT_NODES<-; bailing out!"
        exit 1
  fi
}

function policy_cfg_mds {
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - mds (all but last node)
role-mds/cluster/*.sls slice=[:-1]
EOF
}

function policy_cfg_rgw {
    if [ -z "$SSL" ] ; then
        cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - rgw (first node)
role-rgw/cluster/*.sls slice=[:1]
EOF
    else
        cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - rgw (first node)
role-rgw/cluster/*.sls slice=[:1]
role-rgw-ssl/cluster/*.sls slice=[:1]
EOF
    fi
}

function policy_cfg_igw {
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - igw (first node)
role-igw/cluster/*.sls slice=[:1]
EOF
}

function policy_cfg_nfs_ganesha {
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - NFS-Ganesha (first node)
role-ganesha/cluster/*.sls slice=[:1]
EOF
}
