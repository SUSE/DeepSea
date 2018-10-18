
start lrbd:
  service.running:
    - name: lrbd
    - onlyif: "test -f /usr/sbin/lrbd"

