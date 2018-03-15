
change mon.conf:
  cmd.run:
    - name: "echo 'mon pg warn min per osd = 16' > /srv/salt/ceph/configuration/files/ceph.conf.d/mon.conf"

