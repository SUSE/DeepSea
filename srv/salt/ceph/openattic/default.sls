

install openattic:
  pkg.installed:
    - pkgs:
      - openattic

enable openattic-systemd:
  service.running:
    - name: openattic-systemd
    - enable: True

