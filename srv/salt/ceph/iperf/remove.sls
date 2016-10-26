iperd_stopped:
  service.dead:
    - enable: False
    - name : iperfd


iperfd_service_remove:
  file.absent:
    - name : /usr/lib/systemd/system/iperfd.service


iperfd_service_remove_reload_systemd:
  cmd.run:
    - name: systemctl daemon-reload
    - watch:
      - file: /usr/lib/systemd/system/iperfd.service
