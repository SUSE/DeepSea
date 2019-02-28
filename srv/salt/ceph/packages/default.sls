
ceph:
  pkg.installed:
    - pkgs:
      - ceph
      - ceph-mgr-dashboard
    - refresh: True
    - fire_event: True
