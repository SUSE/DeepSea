
Check pid {{ service }}:
  cmd.run:
    - name: "test \"$(pgrep ceph-{{ service }})\" = \"$(cat /tmp/restart.pid)\""
    - failhard: True

/tmp/restart.pid:
  file.absent

