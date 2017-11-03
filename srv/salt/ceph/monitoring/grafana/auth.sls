{% set user = salt['pillar.get']('grafana_user', 'admin') %}
{% set password = salt['pillar.get']('grafana_password', 'admin') %}
{% set cluster = salt['pillar.get']('cluster', 'ceph') %}

require jq:
  pkg.installed:
    - name: jq
    - fire_event: true
    - refresh: True

{% for grafana_host in salt.saltutil.runner('select.minions', cluster='ceph', roles='grafana') %}

add api token {{ grafana_host }}:
  cmd.run:
    - name: |
        apikey=`curl -s -H "Content-Type: application/json" \
          -XPOST http://{{ user }}:{{ password }}@{{ grafana_host }}:3000/api/auth/keys \
          -d '{ "name": "deepsea", "role": "Admin"}' \
          | jq -r '"grafana_{{ grafana_host }}_token: " + .key'`
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='master') %}
        mkdir -p /srv/pillar/ceph/monitoring/{{ cluster }}/minions/
        if [ -f /srv/pillar/ceph/monitoring/{{ cluster }}/minions/{{ host }}.yml ]; then
            sed -i '/^grafana_{{ grafana_host }}_token:/d' /srv/pillar/ceph/monitoring/{{ cluster }}/minions/{{ host }}.yml
        fi
        echo "$apikey" >> /srv/pillar/ceph/monitoring/{{ cluster }}/minions/{{ host }}.yml
{% endfor %}
    - unless: |
        curl -s -H "Content-Type: application/json" \
          -XGET http://{{ user }}:{{ password }}@{{ grafana_host }}:3000/api/auth/keys \
          | grep deepsea

{% endfor %}
