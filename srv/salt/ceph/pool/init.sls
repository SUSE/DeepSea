
include:
  - .begin
  - .{{ salt['pillar.get']('pool_creation') }}
  - .complete
