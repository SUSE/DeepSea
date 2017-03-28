restart:
  cmd.run:
    - name: "systemctl restart nfs"
    - unless: "systemctl is-failed nfs"
    - fire_event: True

  cmd.run:
    - name: "systemctl restart rpc-statd"
    - unless: "systemctl is-failed rpc-statd"
    - fire_event: True

  cmd.run:
    - name: "systemctl restart rpcbind"
    - unless: "systemctl is-failed rpcbind"
    - fire_event: True

  cmd.run:
    - name: "systemctl restart nfs-ganesha.service"
    - unless: "systemctl is-failed nfs-ganesha.service"
    - fire_event: True
