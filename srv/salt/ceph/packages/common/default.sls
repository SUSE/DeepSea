


stage prep dependencies:
  pkg.installed:
    - pkgs:
      - lsscsi
      - smartmontools
      - pciutils
      - gptfdisk
    - fire_event: True

