
check lock:
  module.run:
    - name: zypper_locks.ready
    - fire_event: True


ceph:
  pkg.installed:
    - pkgs:
      - ceph
    - fire_event: True

