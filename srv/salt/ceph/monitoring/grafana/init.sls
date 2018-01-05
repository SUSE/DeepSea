{% if grains.get('os', '') == 'CentOS' %}

configure_grafana_repo:
  pkgrepo.managed:
    - name: grafana-repo
    - humanname: CentoOS-$releasever - Grafana Repo
    - baseurl: https://packagecloud.io/grafana/stable/el/$releasever/$basearch/
    - gpgcheck: False
    - enabled: True
    - fire_event: True

{% endif %}

grafana:
  pkg.installed:
    - name: grafana
    - fire_event: true
    - refresh: True

grafana-server:
  service.running:
    - enable: true
    - require:
      - pkg: grafana

wait-for-grafana-http:
  cmd.run:
    - require:
      - service: grafana-server
    - name: |
         SLEEP_SECONDS=5
         CURL_CMD="curl -s -H \"Content-Type: application/json\" -XGET http://admin:admin@localhost:3000/api/datasources"
         i=0
         eval $CURL_CMD
         curl_ret=$?
         until [ $curl_ret -eq 0 ] || [ $i -eq 24 ]; do
           sleep $SLEEP_SECONDS
           eval $CURL_CMD
           curl_ret=$?
           i=$((i + 1))
         done;
         if [ $curl_ret -ne 0 ] ; then
             echo "ERROR: The grafana http server failed to start after $((i * SLEEP_SECONDS))s"
         fi
         test $curl_ret -eq 0


add prometheus ds:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/datasources \
          -d @- <<EOF
          { "name": "Prometheus", "type": "prometheus", "access": "proxy", "url": "http://localhost:9090", "isDefault": true }
        EOF
    - unless:
      - curl -s -H "Content-Type: application/json" \
          -XGET http://admin:admin@localhost:3000/api/datasources/name/Prometheus

add node dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/node.json

add cluster dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-cluster.json

add pools dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-pools.json

add osd dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-osd.json

add rbd dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-rbd.json

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') %}

add rgw dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-rgw.json

add rgw-users dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
          -d @/srv/salt/ceph/monitoring/grafana/files/ceph-rgw-users.json

{% else %}

remove rgw dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XDELETE http://admin:admin@localhost:3000/api/dashboards/db/ceph-object-gateway

remove rgw-users dashboard:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XDELETE http://admin:admin@localhost:3000/api/dashboards/db/ceph-object-gateway-users

{% endif %}
