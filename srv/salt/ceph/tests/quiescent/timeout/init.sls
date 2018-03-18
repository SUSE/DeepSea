
{% set id = salt['osd.list']() | first %}

"{{ id }}":
  test.nop 

stop OSD:
  cmd.run:
    - name: "systemctl stop ceph-osd@{{ id }}"

not active+clean:
  module.run:
    - name: osd.ceph_quiescent
    - kwargs:
        timeout: 1
        delay: 1
    - onfail:
        - test: passes

Timeout failed:
  test.fail_without_changes:
    - onlyif:
      - not active+clean

passes:
  test.nop

start OSD:
  cmd.run:
    - name: "systemctl start ceph-osd@{{ id }}"

