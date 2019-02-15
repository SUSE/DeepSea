
/etc/ceph/iscsi-gateway.cfg:
  file.managed:
    - source:
      - salt://ceph/igw/files/iscsi-gateway.cfg.j2
    - template: jinja
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - context:
      client: "client.igw.{{ grains['host'] }}"

