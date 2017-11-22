remove_rgw_exporter_cron_job:
  cron.absent:
    - identifier: 'Prometheus rgw_exporter cron job'
