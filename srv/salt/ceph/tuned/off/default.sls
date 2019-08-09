
stop tuned:
  service.dead:
    - name: tuned
    - enable: False

/etc/tuned/ceph-latency/:
  file.absent

/etc/tuned/ceph-throughput/:
  file.absent

/etc/tuned/ceph-mon/:
  file.absent

/etc/tuned/ceph-mgr/:
  file.absent

/etc/tuned/ceph-osd/:
  file.absent

