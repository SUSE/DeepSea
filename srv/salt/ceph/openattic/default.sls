

install openattic:
  pkg.installed:
    - pkgs:
      - openattic

#enable openattic-rpcd:
#  service.running:
#    - name: openattic-rpcd
#    - enable: True

enable openattic-systemd:
  service.running:
    - name: openattic-systemd
    - enable: True

