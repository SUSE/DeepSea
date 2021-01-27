update salt:
  pkg.latest:
    - pkgs:
      - salt-minion 
    - dist-upgrade: True
    - failhard: True

restart salt-minion:
  cmd.run:
    - name: "salt-call service.restart salt-minion"
    - bg: True
    - failhard: True
