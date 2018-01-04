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
    - require: grafana-server
    - watch: grafana
    - name: |
         SLEEP_SECONDS=5
         CURL_CMD="curl -s -H \"Content-Type: application/json\" \
           -XGET http://admin:admin@localhost:3000/api/datasources"
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
