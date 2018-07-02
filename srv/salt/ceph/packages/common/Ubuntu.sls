
stage prep dependencies:
  pkg.installed:
    - pkgs:
      - lshw
      - lsscsi
      - pciutils
      - gdisk
      - python3-boto
      - python3-rados
      - iperf
      - jq
    - fire_event: True
    - refresh: True

