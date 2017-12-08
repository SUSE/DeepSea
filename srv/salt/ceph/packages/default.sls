
ceph:
  pkg.installed:
    - pkgs:
      - ceph
    - refresh: True
    - fire_event: True

