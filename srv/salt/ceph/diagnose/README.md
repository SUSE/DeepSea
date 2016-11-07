# Diagnoses tools

This README describes the diagnosis tools:

- ceph.diagnose.ping
- ceph.diagnose.iperf3
- ceph.diagnose.iperf3-concurrent

Notes:

As of deepsea version 0.6.7 deepsea sets the salt masters state-output. So all
diagnose tests will give no output unless ran with the a state output option for
example:

    --state-output=changes

## ceph.diagnose.ping

This diagnose command runs a ping test on every salt managed node with pillar
role cluster='ceph' to every ipv4 address on each other salt managed node with
the pillar role cluster='ceph'. Each targeted ipv4 address is pinged
concurrently by all remote targeted minions.

To execute the ping diagnosis test

    salt-run --state-output=changes state.orch ceph.diagnose.ping

Notes:

- ceph.diagnose.ping is recommended to only be run during service downtime.
- Since this test attempts to ping each target ipv4 address 4 times, it can
  take some time to execute on larger clusters with multiple networks.

Run time:

Excluding setup and tear down time the tests run time can be estimated as:

   Nodes * networks attached * 4 seconds

## ceph.diagnose.iperf3

This diagnose command runs an iperf3 bandwidth test on every salt managed node
with pillar role cluster='ceph' to every ipv4 address on each other salt
managed node with the pillar role cluster='ceph'. Each targeted ipv4 link is
tested serially. Consequently this test will have a long run time on large
clusters.

To execute the iperf3 diagnosis test

    salt-run --state-output=changes state.orch ceph.diagnose.iperf3

Run time:

Excluding setup and tear down time the tests run time can be estimated as:

   Nodes * (Nodes -1) * networks attached * 10 seconds

Notes:

- ceph.diagnose.iperf3 is strongly recommended to only be run during service
  downtime.
- This test is bandwidth testing each ipv4 link on your cluster for 10 seconds
  (by default) running this on a production cluster will impact cluster
  performance.
- Since this test only tests one ipv4 link between your ceph nodes at a time it
  can have a long run time on larger clusters.

## ceph.diagnose.iperf3-concurrent

This diagnose command runs an iperf3 bandwidth test on every salt managed node
with pillar role cluster='ceph' to every ipv4 address on each other salt
managed node with the pillar role cluster='ceph'. Each targeted ipv4 link is
tested in parallel when posable. Consequently this test will run significantly
faster than the diagnosis command ceph.diagnose.iperf3 but may not give the same
results and this difference may suggest network saturation issues at the switch
infrastructure level.

To execute the iperf3-concurrent diagnosis test

    salt-run --state-output=changes state.orch ceph.diagnose.iperf3-concurrent

Run time:

The concurrency will at best be the number of nodes divided by 2 and rounded
down to the closest integer.

Excluding setup and tear down time the tests run time can be estimated as:

   Nodes * (Nodes -1) / ${concurrency} * networks attached * 10 seconds.

Notes:

- ceph.diagnose.iperf3-concurrent should only be run during service downtime.
- Running this on a production cluster will impact cluster performance greatly.
- This test should saturate each ipv4 link on your cluster for 10 seconds
  (by default) concurrently, and repeating this saturation for each combination
  of ipv4 links for the test runtime.
- Since this test tests all ipv4 link between your ceph nodes it can have a
  long run time on larger clusters, but it will execute significantly faster
  than the ceph.diagnose.iperf3 operation.
