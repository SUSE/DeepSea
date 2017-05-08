
salt-api:
  pkg.installed:
    - pkgs:
      - salt-api
    - fire_event: True
