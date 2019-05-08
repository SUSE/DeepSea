
aa-teardown:
  cmd.run

apparmor:
  service.dead:
    - enable: False

uninstall apparmor:
  pkg.removed:
    - pkgs:
      - apparmor
      - apparmor-utils
