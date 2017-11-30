# Ensure the cron job does not exist, otherwise it will not be (re-)added
# with this content.
remove_rgw_exporter_cron_job:
  cron.absent:
    - identifier: 'Prometheus rgw_exporter cron job'

install_rgw_exporter_cron_job:
  cron.present:
    - name: '/var/lib/prometheus/node-exporter/ceph_rgw.py > /var/lib/prometheus/node-exporter/ceph_rgw.prom 2> /dev/null'
    - minute: '*/5'
    - identifier: 'Prometheus rgw_exporter cron job'
