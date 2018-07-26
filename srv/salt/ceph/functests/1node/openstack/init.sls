# NOTE:
# - These tests are destructive; the default test will trash any existing
#   non-prefixed openstack pools and users.
#
# TODO:
# - Verify the various users can access the appropriate pools and check
#   ceph status, but can't do anything else.
# - Add tests for the openstack.integrate runner itself, to make sure it
#   returns correct data.

include:
  - .default
  - .prefix
