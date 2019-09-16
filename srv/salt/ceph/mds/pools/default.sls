
{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') == [] %}

prevent empty rendering:
  test.nop:
    - name: skip

{% else %}

{# create cephfs_data pool iif it doesn't exist and no fs instance exists #}
cephfs data:
  cmd.run:
    - name: "ceph osd pool create cephfs_data 256"
    - onlyif:
      - 'test -z "$(rados lspools | grep cephfs_data)"'
      - 'test -z "$(ceph fs ls | grep ^name)"'

cephfs data pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable cephfs_data cephfs || :"

{# create cephfs_metadata pool iif it doesn't exist and no fs instance exists #}
cephfs metadata:
  cmd.run:
    - name: "ceph osd pool create cephfs_metadata 64"
    - onlyif:
      - 'test -z "$(rados lspools | grep cephfs_metadata)"'
      - 'test -z "$(ceph fs ls | grep ^name)"'

cephfs metadata pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable cephfs_metadata cephfs || :"

cephfs:
  cmd.run:
    - name: "ceph fs new cephfs cephfs_metadata cephfs_data"
    - unless: "ceph fs ls | grep -q ^name"

{% endif %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

