# This file is part of the DeepSea integration test suite

#
# functions for generating storage proposals
#

PROPOSALSDIR="/srv/pillar/ceph/proposals"
POLICY_CFG="$PROPOSALSDIR/policy.cfg"

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
  cat <<EOF > $POLICY_CFG
# Cluster assignment
cluster-ceph/cluster/*.sls
# Common configuration
config/stack/default/global.yml
config/stack/default/ceph/cluster.yml
# Role assignment - master
role-master/cluster/${MASTER_MINION}.sls
# Role assignment - admin
role-admin/cluster/*.sls
EOF
}

function policy_cfg_mon_flex {
  test -n "$STORAGE_NODES" # set in initialization_sequence
  test "$STORAGE_NODES" -gt 0
  if [ "$STORAGE_NODES" -lt 4 ] ; then
    echo "Undersized cluster ($STORAGE_NODES nodes)"
    policy_cfg_one_mon
  else
    policy_cfg_three_mons
  fi
}

function policy_cfg_one_mon {
  cat <<EOF >> $POLICY_CFG
# Role assignment - 1 mon, 1 mgr
role-mon/cluster/*.sls slice=[:1]
role-mgr/cluster/*.sls slice=[:1]
EOF
}

function policy_cfg_three_mons {
  cat <<EOF >> $POLICY_CFG
# Role assignment - 3 mons, 3 mgrs
role-mon/cluster/*.sls slice=[:3]
role-mgr/cluster/*.sls slice=[:3]
EOF
}

function _initialize_minion_configs_array {
    local DIR=$1

    shopt -s nullglob
    pushd $DIR >/dev/null
    MINION_CONFIGS_ARRAY=(*.yaml *.yml)
    echo "Made global array containing the following files (from ->$DIR<-):"
    printf '%s\n' "${MINION_CONFIGS_ARRAY[@]}"
    popd >/dev/null
    shopt -u nullglob
}

function _initialize_osd_configs_array {
    local DIR=$1

    shopt -s nullglob
    pushd $DIR >/dev/null
    OSD_CONFIGS_ARRAY=(*.yaml *.yml)
    echo "Made global array containing the following OSD configs (from ->$DIR<-):"
    printf '%s\n' "${OSD_CONFIGS_ARRAY[@]}"
    popd >/dev/null
    shopt -u nullglob
}

function _custom_osd_config {
    local PROFILE=$1
    local FILENAME=""
    for i in "${OSD_CONFIGS_ARRAY[@]}" ; do
        case "$i" in
            $PROFILE) FILENAME=$i ; break ;;
            ${PROFILE}.yaml) FILENAME=$i ; break ;;
            ${PROFILE}.yml) FILENAME=$i ; break ;;
        esac
    done
    if [ -z "$FILENAME" ] ; then
        echo "Custom OSD profile $PROFILE not found. Bailing out!"
        exit 1
    fi
    echo "$FILENAME"
}

function _random_osd_config {
    # the bare config file names are assumed to already be in OSD_CONFIGS_ARRAY
    # (accomplished by calling _initialize_osd_configs_array first)
    OSD_CONFIGS_ARRAY_LENGTH="${#OSD_CONFIGS_ARRAY[@]}"
    local INDEX=$((RANDOM % OSD_CONFIGS_ARRAY_LENGTH))
    echo "${OSD_CONFIGS_ARRAY[$INDEX]}"

}

function random_or_custom_storage_profile {
    test "$STORAGE_PROFILE"
    test "$STORAGE_PROFILE" = "random" -o "$STORAGE_PROFILE" = "custom"
    #
    # choose OSD configuration from qa/osd-config/ovh
    #
    local SOURCEDIR="$BASEDIR/osd-config/ovh"
    _initialize_osd_configs_array $SOURCEDIR
    local SOURCEFILE=""
    case "$STORAGE_PROFILE" in
        random) SOURCEFILE=$(_random_osd_config) ;;
        custom) SOURCEFILE=$(_custom_osd_config $CUSTOM_STORAGE_PROFILE) ;;
    esac
    test "$SOURCEFILE"
    file $SOURCEDIR/$SOURCEFILE
    #
    # prepare new profile, which will be exactly the same as the default
    # profile except the files in stack/default/ceph/minions/ will be
    # overwritten with our chosen OSD configuration
    #
    cp -a $PROPOSALSDIR/profile-default $PROPOSALSDIR/profile-$STORAGE_PROFILE
    local DESTDIR="$PROPOSALSDIR/profile-$STORAGE_PROFILE/stack/default/ceph/minions"
    _initialize_minion_configs_array $DESTDIR
    for DESTFILE in "${MINION_CONFIGS_ARRAY[@]}" ; do
        cp $SOURCEDIR/$SOURCEFILE $DESTDIR/$DESTFILE
    done
    echo "Your $STORAGE_PROFILE storage profile $SOURCEFILE has the following contents:"
    cat $DESTDIR/$DESTFILE
    ls -lR $PROPOSALSDIR
}

function policy_cfg_storage {
    test -n "$CLIENT_NODES"
    test -n "$STORAGE_PROFILE"

    if [ "$CLIENT_NODES" -eq 0 ] ; then
        cat <<EOF >> $POLICY_CFG
# Hardware Profile
profile-$STORAGE_PROFILE/cluster/*.sls
profile-$STORAGE_PROFILE/stack/default/ceph/minions/*yml
EOF
    elif [ "$CLIENT_NODES" -ge 1 ] ; then
        cat <<EOF >> $POLICY_CFG
# Hardware Profile
profile-$STORAGE_PROFILE/cluster/*.sls slice=[:-$CLIENT_NODES]
profile-$STORAGE_PROFILE/stack/default/ceph/minions/*yml slice=[:-$CLIENT_NODES]
EOF
    else
        echo "Unexpected number of client nodes ->$CLIENT_NODES<-; bailing out!"
        exit 1
    fi
}

function storage_profile_from_policy_cfg {
    local BUFFER=$(grep --max-count 1 '^profile-' $POLICY_CFG)
    perl -e '"'"$BUFFER"'" =~ m/profile-(\w+)/; print "$1\n";'
}

function policy_remove_storage_node {
    local NODE_TO_DELETE=$1

    echo "Before"
    ls -1 $PROPOSALSDIR/profile-$STORAGE_PROFILE/cluster/
    ls -1 $PROPOSALSDIR/profile-$STORAGE_PROFILE/stack/default/ceph/minions/

    local basedirsls=$PROPOSALSDIR/profile-$STORAGE_PROFILE/cluster
    local basediryml=$PROPOSALSDIR/profile-$STORAGE_PROFILE/stack/default/ceph/minions
    mv $basedirsls/${NODE_TO_DELETE}.sls $basedirsls/${NODE_TO_DELETE}.sls-DISABLED
    mv $basediryml/${NODE_TO_DELETE}.yml $basedirsls/${NODE_TO_DELETE}.yml-DISABLED

    echo "After"
    ls -1 $PROPOSALSDIR/profile-$STORAGE_PROFILE/cluster/
    ls -1 $PROPOSALSDIR/profile-$STORAGE_PROFILE/stack/default/ceph/minions/
}

function policy_cfg_mds {
    test -n "$CLIENT_NODES"

    if [ "$CLIENT_NODES" -eq 0 ] ; then
        cat <<EOF >> $POLICY_CFG
# Role assignment - mds (all nodes)
role-mds/cluster/*.sls
EOF
    elif [ "$CLIENT_NODES" -ge 1 ] ; then
        cat <<EOF >> $POLICY_CFG
# Role assignment - mds (all non-client nodes)
role-mds/cluster/*.sls slice=[:-$CLIENT_NODES]
EOF
    else
        echo "Unexpected number of client nodes ->$CLIENT_NODES<-; bailing out!"
        exit 1
    fi
}

function policy_cfg_rgw {
    if [ -z "$SSL" ] ; then
        cat <<EOF >> $POLICY_CFG
# Role assignment - rgw (first node)
role-rgw/cluster/*.sls slice=[:1]
EOF
    else
        cat <<EOF >> $POLICY_CFG
# Role assignment - rgw (first node)
role-rgw/cluster/*.sls slice=[:1]
role-rgw-ssl/cluster/*.sls slice=[:1]
EOF
    fi
}

function policy_cfg_igw {
    cat <<EOF >> $POLICY_CFG
# Role assignment - igw (first node)
role-igw/cluster/*.sls slice=[:1]
EOF
}

function policy_cfg_nfs_ganesha {
    cat <<EOF >> $POLICY_CFG
# Role assignment - NFS-Ganesha (first node)
role-ganesha/cluster/*.sls slice=[:1]
EOF
}
