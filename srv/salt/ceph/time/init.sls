

include:
  - .begin
  - .{{ salt['pillar.get']('time_service') }}
  - .complete

