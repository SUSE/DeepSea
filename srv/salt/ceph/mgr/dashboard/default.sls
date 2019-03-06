
ceph mgr dashboard:
  pkg.installed:
    - pkgs:
      - ceph-mgr-dashboard
    - refresh: True
    - fire_event: True
