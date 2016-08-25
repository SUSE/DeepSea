
check lock:
  module.run:
    - name: zypper_locks.ready
    - fire_event: True


ceph:
  pkg.installed:
    - pkgs:
      - ceph
    - fire_event: True

#ceph install:
#  cmd.run:
#    - name: "zypper --non-interactive --no-gpg-checks in ceph"
#    - require:
#      - module: check lock
#    - fire_event: True

#ceph install:
#  pkg.installed:
#    - name: "ceph"
#    - require:
#      - module: check lock
#    - fire_event: True
