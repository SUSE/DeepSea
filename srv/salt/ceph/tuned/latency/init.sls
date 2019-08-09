
include:
  - .{{ salt['pillar.get']('tuned_latency', 'default') }}
