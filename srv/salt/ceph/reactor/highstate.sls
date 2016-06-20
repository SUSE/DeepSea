highstate_run:
  cmd.state.highstate:
    - tgt: {{ data['id'] }}

