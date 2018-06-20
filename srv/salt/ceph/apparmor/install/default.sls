
install apparmor:
  pkg.installed:
    - pkgs:
      - apparmor
      - apparmor-utils

apparmor:
  service.running:
    - enable: True
