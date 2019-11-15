
include:
  - .{{ salt['pillar.get']('tuned_throughput', 'default') }}
