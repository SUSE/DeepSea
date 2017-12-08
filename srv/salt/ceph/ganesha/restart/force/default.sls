restart nfs-ganesha:
  module.run:
    - name: service.restart
    - m_name: nfs-ganesha
