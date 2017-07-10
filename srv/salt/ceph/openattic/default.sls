

install openattic:
  pkg.installed:
    - pkgs:
      - openattic

enable openattic-systemd:
  service.running:
    - name: openattic-systemd
    - enable: True

/etc/sysconfig/openattic:
  file.append:
    - text: |
        SALT_API_HOST="{{ salt['pillar.get']('master_minion') }}"
        SALT_API_PORT=8000
        SALT_API_EAUTH="sharedsecret"
        SALT_API_USERNAME="admin"
        SALT_API_SHARED_SECRET="{{ salt['pillar.get']('salt_api_shared_secret') }}"
