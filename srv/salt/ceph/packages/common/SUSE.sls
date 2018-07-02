
stage prep dependencies:
  pkg.installed:
    - pkgs:
      - ses-release
      - hwinfo
      - lsscsi
      - pciutils
      - gptfdisk
      - python3-boto
      - python3-rados
      - iperf
      - lsof
      - jq
    - fire_event: True
    - refresh: True

