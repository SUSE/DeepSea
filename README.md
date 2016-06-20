# Pillar Prototype
These salt files are intended to allow the creation and management of multiple ceph clusters with a single salt master.  

The diagram should explain the intended flow for the orchestration runners and related salt states.  

## Status
This is alpha at best.  It works, but runners need refactoring, commenting, correct returns and unit tests.  Several decisions still remain and a few files have notes alluding to missing functionality.  Only a single cluster named `ceph` has been tested.


