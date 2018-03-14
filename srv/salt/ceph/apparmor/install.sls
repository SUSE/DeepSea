
zypper -n in -t pattern apparmor:
  cmd.run

apparmor:
  service.running:
    - enable: True
