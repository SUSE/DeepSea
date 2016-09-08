


install lrbd:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in lrbd"

enable lrbd:
  service.running:
    - name: lrbd
    - enable: True

reload lrbd:
  module.run:
    - name: service.restart
    - m_name: lrbd
