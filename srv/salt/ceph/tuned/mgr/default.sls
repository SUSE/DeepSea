/etc/tuned/ceph-mgr/tuned.conf:
  file.managed:
    - source: salt://ceph/tuned/files/ceph-mgr/tuned.conf
    - makedirs: True
    - user: root
    - group: root
    - mode: 644

# We are explicitly using service.enabled and service.runnig
# separately because it triggers a reload if the service is started and 
# _then_ reloaded. Force it the other way around.
start tuned ceph mgr:
  service.enabled:
    - name: tuned

start tuned ceph mgr:
  service.running:
    - name: tuned

apply tuned ceph mgr:
  cmd.run:
    - name: 'tuned-adm profile ceph-mgr'
