
Check pid:
  cmd.run:
    - name: "[ `pgrep radosgw` ==  `cat /tmp/restart.pid` ]"
    - failhard: True

/tmp/restart.pid:
  file.absent

