update salt:
  pkg.latest:
    - pkgs:
      - salt-minion 
      - salt-master
