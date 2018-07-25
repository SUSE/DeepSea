
install apparmor:
  pkg.installed:
    - pkgs:
      - patterns-base-apparmor
      - apparmor-utils

apparmor:
  service.running:
    - enable: True

