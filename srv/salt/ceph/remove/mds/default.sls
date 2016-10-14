
remove mon nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') == [] %}

fail mds:
  cmd.run:
    - name: "ceph mds fail 0"

remove cephfs:
  cmd.run:
    - name: "ceph fs rm cephfs --yes-i-really-mean-it"

remove metadata:
  cmd.run:
    - name: "ceph osd pool delete cephfs_metadata cephfs_metadata --yes-i-really-really-mean-it"

remove data:
  cmd.run:
    - name: "ceph osd pool delete cephfs_data cephfs_data --yes-i-really-really-mean-it"

{% endif %}

