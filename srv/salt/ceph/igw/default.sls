
lrbd:
  pkg.installed:
    - pkgs:
      - lrbd

enable lrbd:
  service.running:
    - name: lrbd
    - enable: True

reload lrbd:
  module.run:
    - name: service.restart
    - m_name: lrbd
