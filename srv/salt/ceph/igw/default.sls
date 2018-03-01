
lrbd:
  pkg.installed:
    - pkgs:
      - lrbd
    - refresh: True

enable lrbd:
  service.running:
    - name: lrbd
    - enable: True
