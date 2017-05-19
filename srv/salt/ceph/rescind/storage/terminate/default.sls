
storage nop:
  test.nop

{% if 'storage' not in salt['pillar.get']('roles') %}

# systemctl stop ceph-osd@id can hang
stop osds:
  cmd.run:
    - name: "systemctl stop ceph-osd.target"

terminate osds:
  cmd.run:
    - name: "pkill ceph-osd"
    - onlyif: "pgrep ceph-osd"

sleep 3 seconds:
  module.run:
    - name: test.sleep
    - length: 3

kill osds:
  cmd.run:
    - name: "pkill -9 ceph-osd"
    - onlyif: "pgrep ceph-osd"

{% endif %}
