

install openattic:
  pkg.installed:
    - pkgs:
      - openattic
    - refresh: True

configure salt-api:
  module.run:
    - name: openattic.configure_salt_api
    - kwargs:
      hostname: "{{ salt['pillar.get']('master_minion') }}"
      port: 8000
      username: "admin"
      sharedsecret: "{{ salt['pillar.get']('salt_api_shared_secret') }}"

configure grafana:
  module.run:
    - name: openattic.configure_grafana
    - kwargs:
      hostname: "{{ salt['pillar.get']('master_minion') }}"

enable openattic-systemd:
  service.running:
    - name: openattic-systemd
    - enable: True
