#!/bin/bash
#
# Dashboard sanity checks
#
# takes a single argument, BASEDIR, for sourcing common/common.sh

BASEDIR=${1}
source $BASEDIR/common/common.sh

set -ex

# -----------------------------------------------------------------
# sanity_dashboard_noop
# -----------------------------------------------------------------
#
# Description: do nothing
#
echo "Inside sanity_dashboard.sh - doing nothing"

echo "dashboard sanity checks OK"
