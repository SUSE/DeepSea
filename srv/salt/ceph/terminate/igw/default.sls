
stop lrbd:
  service.dead:
    - name: lrbd
    - onlyif: "test -f /usr/sbin/lrbd"

