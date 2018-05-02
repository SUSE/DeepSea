
absent OSDs:
  cmd.run:
    - name: /bin/false
    - onlyif: ceph osd ls | egrep -q '^0$'
