
demo pool:
  cmd.run:
    - name: "ceph osd pool create iscsi-images 128"
    - unless: "ceph osd pool ls | grep -q iscsi-images$"
    - fire_event: True

demo image:
  cmd.run:
    - name: "rbd -p iscsi-images create demo --size=1024"
    - unless: "rbd -p iscsi-images ls | grep -q demo$"
    - fire_event: True

lrbd:
  pkg.installed:
    - pkgs:
      - lrbd

enable lrbd:
  service.running:
    - name: lrbd
    - enable: True

reload lrbd:
  module.run:
    - name: service.restart
    - m_name: lrbd
