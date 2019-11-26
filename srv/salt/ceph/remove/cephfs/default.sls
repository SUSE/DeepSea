
remove mds nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') == [] %}

fail mds daemons:
  cmd.run:
    - name: "ceph fs fail cephfs || :"

remove cephfs:
  cmd.run:
    - name: "ceph fs rm cephfs --yes-i-really-mean-it || :"

remove metadata:
  cmd.run:
    - name: "ceph osd pool delete cephfs_metadata cephfs_metadata --yes-i-really-really-mean-it || :"

remove data:
  cmd.run:
    - name: "ceph osd pool delete cephfs_data cephfs_data --yes-i-really-really-mean-it || :"

{% endif %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

