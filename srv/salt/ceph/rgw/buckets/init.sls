

include:
  - .{{ salt['pillar.get']('rgw_buckets', 'default') }}
