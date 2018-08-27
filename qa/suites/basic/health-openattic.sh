#!/bin/bash
#
# wrapper around health-ok.sh for deploying a Ceph cluster with openATTIC
#

SCRIPTNAME=$(basename ${0})
BASEDIR=$(readlink -f "$(dirname ${0})/../..")
test -d $BASEDIR
[[ $BASEDIR =~ \/qa$ ]]

source $BASEDIR/suites/basic/health-ok.sh --cli --client-nodes=1 --mds --igw --min-nodes=2 --nfs-ganesha --openattic --rgw

