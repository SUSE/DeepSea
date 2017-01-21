
stop fio:
  service.dead:
    - name: fio

remove fio service file:
  file.absent:
    - name: /etc/systemd/system/fio.service
