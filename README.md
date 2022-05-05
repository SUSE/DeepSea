[![Build Status](https://travis-ci.org/SUSE/DeepSea.svg?branch=master)](https://travis-ci.org/SUSE/DeepSea)
# DeepSea
A collection of [Salt](https://saltstack.com/salt-open-source/) files for deploying, managing and automating [Ceph](https://ceph.com/).

The goal is to manage multiple Ceph clusters with a single salt master. At this time, only a single Ceph cluster can be managed.

This [diagram](deepsea.png) should explain the intended flow for the orchestration runners and related salt states.

## Status

DeepSea is no longer being actively developed since [cephadm](https://docs.ceph.com/en/octopus/cephadm/) was added to the Ceph Octopus release.

The [SES6 branch](https://github.com/SUSE/DeepSea/tree/SES6) (v0.9.x) contains the most recent release of DeepSea, which supports deploying Ceph Nautilus.