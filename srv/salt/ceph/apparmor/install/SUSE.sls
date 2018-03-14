
patterns-base-apparmor:
  pkg.installed

apparmor:
  service.running:
    - enable: True

