update deepsea:
  pkg.latest:
    - pkgs:
      - deepsea
      - salt-master
      - salt-minion
    - dist-upgrade: True
