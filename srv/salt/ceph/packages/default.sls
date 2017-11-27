
ceph:
  pkg.latest:
    - pkgs:
      - ceph
    - dist-upgrade: True
    - fire_event: True
