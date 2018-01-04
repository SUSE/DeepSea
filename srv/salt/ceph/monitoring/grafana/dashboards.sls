{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='grafana') %}
{% set auth_header = 'Authorization: Bearer {}'.format(salt['pillar.get']('grafana_{}_token'.format(host), '')) %}

add prometheus ds:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/datasources \
          -d @- <<EOF
          { "name": "Prometheus", "type": "prometheus", "access": "proxy", "url": "http://localhost:9090", "isDefault": true }
        EOF
    - unless:
      - curl -s -H "Content-Type: application/json" \
          -XGET http://{{ host }}:3000/api/datasources/name/Prometheus

add node dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/node.json

add cluster dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-cluster.json

add pools dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-pools.json

add osd dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-osd.json

add rbd dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-rbd.json

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') %}

add rgw dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-rgw.json

add rgw-users dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XPOST http://{{ host }}:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-rgw-users.json

{% else %}

remove rgw dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XDELETE http://{{ host }}:3000/api/dashboards/db/ceph-object-gateway

remove rgw-users dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -H "{{ auth_header }}" \
          -XDELETE http://{{ host }}:3000/api/dashboards/db/ceph-object-gateway-users

{% endif %}

{% endfor %}

