
absent OSDs:
  cmd.run:
    - name: /bin/false
    - unless: ceph osd ls | egrep -q '^0$|^1$'
