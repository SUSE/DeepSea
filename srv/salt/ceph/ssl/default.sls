{% set CN = salt['deepsea.ssl_cert_cn_wildcard']() %}

create CA:
  module.run:
    - name: tls.create_ca
    - ca_name: deepsea
    - days: 730  # 2 years
    - CN: {{ salt['deepsea.ssl_ca_cert_cn']() }}
    - cacert_path: /etc/ssl
    - fire_event: True

create cert request:
  module.run:
    - name: tls.create_csr
    - ca_name: deepsea
    - CN: "{{ CN }}"
    - subjectAltName:
      - "DNS:{{ CN }}"
    - cacert_path: /etc/ssl
    - fire_event: True

create signed cert:
  module.run:
    - name: tls.create_ca_signed_cert
    - ca_name: deepsea
    - CN: "{{ CN }}"
    - days: 730  # 2 years
    - cacert_path: /etc/ssl
    - fire_event: True

/srv/salt/ceph/ssl/cache/deepsea_ca_cert.crt:
  file.managed:
    - source: /etc/ssl/deepsea/deepsea_ca_cert.crt
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - replace: True
    - fire_event: True
