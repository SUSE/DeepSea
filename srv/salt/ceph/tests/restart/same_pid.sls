
Check pid:
  cmd.run:
    - name: "[ `pgrep ceph-{{ service }}` ==  `cat /tmp/restart.pid` ]"
    - failhard: True

/tmp/restart.pid:
  file.absent

