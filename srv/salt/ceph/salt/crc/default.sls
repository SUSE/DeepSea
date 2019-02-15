/etc/salt/minion:
  file.append:
    - text:
      - "server_id_use_crc: adler32"
