{% if 'master' in salt['pillar.get']('roles') %}
ceph exporter package:
  pkg.installed:
    - name: golang-github-digitalocean-ceph_exporter
    - fire_event: True

start ceph exporter:
  service.running:
    - name: prometheus-ceph_exporter
    - enable: True
{% endif %}
