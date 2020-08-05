aa-enabled:
  cmd.run:
    - onfail:
      - test: apparmor

aa-teardown:
  cmd.run:
    - onlyif:
      - which aa-teardown
    - onfail:
      - test: apparmor

stop apparmor:
  service.dead:
    - enable: False

uninstall apparmor:
  pkg.removed:
    - pkgs:
      - apparmor
      - apparmor-utils

apparmor:
  test.nop
