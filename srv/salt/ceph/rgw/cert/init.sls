

include:
  - .{{ salt['pillar.get']('rgw_cert', 'default') }}
