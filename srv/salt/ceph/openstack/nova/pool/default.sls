
nova pool:
  cmd.run:
    - name: "ceph osd pool create nova 128"
    - unless: "ceph osd pool ls | grep -q nova$"
    - fire_event: True

{{ prefix }}nova pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable {{ prefix }}vms rbd || :"

