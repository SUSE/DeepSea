
remove mon nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') == [] %}

remove rgw root:
  cmd.run:
    - name: "ceph osd pool delete .rgw.root .rgw.root --yes-i-really-really-mean-it"

remove rgw control:
  cmd.run:
    - name: "ceph osd pool delete default.rgw.control default.rgw.control --yes-i-really-really-mean-it"

remove rgw data.root:
  cmd.run:
    - name: "ceph osd pool delete default.rgw.data.root default.rgw.data.root --yes-i-really-really-mean-it"

remove rgw gc:
  cmd.run:
    - name: "ceph osd pool delete default.rgw.gc default.rgw.gc --yes-i-really-really-mean-it"

remove rgw log:
  cmd.run:
    - name: "ceph osd pool delete default.rgw.log default.rgw.log --yes-i-really-really-mean-it"

remove rgw users.uid:
  cmd.run:
    - name: "ceph osd pool delete default.rgw.users.uid default.rgw.users.uid --yes-i-really-really-mean-it"

{% endif %}

