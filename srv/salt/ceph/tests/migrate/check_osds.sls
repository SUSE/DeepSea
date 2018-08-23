
check:
  osd.correct:
    - device: {{ salt['file.read']('/tmp/checklist') }}

