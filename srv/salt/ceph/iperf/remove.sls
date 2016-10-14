iperd_stopped:
  service.running:
    - enable: False
    - name : iperfd
    - running: False


iperfd_service_remove:
  file.absent:
    - name : /usr/lib/systemd/system/iperfd.service
