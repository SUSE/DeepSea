


stage prep dependencies:
  pkg.installed:
    - pkgs:
      - lsscsi
      - pciutils
      - gptfdisk
    - fire_event: True

