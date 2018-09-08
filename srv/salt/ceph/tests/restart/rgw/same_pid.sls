
Check pid radosgw:
  cmd.run:
    - name: "test \"$(pgrep radosgw)\" = \"$(cat /tmp/restart.pid)\""
    - failhard: True

/tmp/restart.pid:
  file.absent

