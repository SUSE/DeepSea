restart nfs:
  module.run:
    - name: service.restart
    - m_name: nfs

restart rpc-statd:
  module.run:
    - name: service.restart
    - m_name: rpc-statd

restart rpcbind:
  module.run:
    - name: service.restart
    - m_name: rpcbind

restart nfs-ganesha:
  module.run:
    - name: service.restart
    - m_name: nfs-ganesha
