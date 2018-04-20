
{% set master = salt['master.minion']() %}

install openattic:
  pkg.installed:
    - pkgs:
      - openattic
    - refresh: True

configure salt-api:
  module.run:
    - name: openattic.configure_salt_api
    - kwargs:
      hostname: "{{ master }}"
      port: 8000
      username: "admin"
      sharedsecret: "{{ salt['pillar.get']('salt_api_shared_secret') }}"

configure grafana:
  module.run:
    - name: openattic.configure_grafana
    - kwargs:
      hostname: "{{ master }}"

enable openattic-systemd:
  service.running:
    - name: openattic-systemd
    - enable: True
