grafana:
  pkg.installed:
    - fire_event: true

grafana-server:
  service.running:
    - enable: true
    - require:
      - pkg: grafana
    - watch:
      - file: /etc/grafana/grafana.ini
  file.exists:
    - name: /var/lib/grafana
    - failhard: True

grafana-dashboards-ceph:
  pkg.installed:
    - fire_event: true

/etc/grafana/grafana.ini:
  file.replace:
    - pattern: |
        \[dashboards\.json\]
        ;*enabled = .+
        ;?path = .*
    - repl: |
        [dashboards.json]
        enabled = true
        path = /var/lib/grafana-dashboards-ceph

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
