
update {{ service }}.conf:
  cmd.run:
    - name: "date +\\#\\ %c > /srv/salt/ceph/configuration/files/ceph.conf.d/{{ service }}.conf"


