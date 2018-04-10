
{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') == [] %}

prevent empty rendering:
  test.nop:
    - name: skip

{% else %}

cephfs data:
  cmd.run:
    - name: "ceph osd pool create cephfs_data 128"
    - unless:
      - "rados lspools | grep -q cephfs_data"
      - "ceph fs ls | grep -q ^name"

cephfs data pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable cephfs cephfs_data || :"

cephfs metadata:
  cmd.run:
    - name: "ceph osd pool create cephfs_metadata 128"
    - unless:
      - "rados lspools | grep -q cephfs_metadata"
      - "ceph fs ls | grep -q ^name"

cephfs metadata pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable cephfs cephfs_metadata || :"

cephfs:
  cmd.run:
    - name: "ceph fs new cephfs cephfs_metadata cephfs_data"
    - unless: "ceph fs ls | grep -q ^name"

{% endif %}

/var/cache/salt/master/jobs:
  file.directory:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - recurse:
      - user
      - group

