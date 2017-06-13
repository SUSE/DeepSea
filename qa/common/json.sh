#
# This file is part of the DeepSea integration test suite
#

function json_total_nodes {
  # total number of nodes in the cluster
  salt --static --out json '*' test.ping | jq '. | length'
}

function _json_nodes_of_role_x {
  local ROLE=$1
  salt --static --out json "$SALT_MASTER" test.ping | jq '. | length'
}

function json_storage_nodes {
  # number of storage nodes in the cluster
  _json_nodes_of_role_x storage
}
