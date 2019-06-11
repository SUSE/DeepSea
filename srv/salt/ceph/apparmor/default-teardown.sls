
aa-teardown:
  cmd.run:
    - onlyif:
      - which aa-teardown

apparmor:
  service.dead:
    - enable: False

uninstall apparmor:
  pkg.removed:
    - pkgs:
      - apparmor
      - apparmor-utils
