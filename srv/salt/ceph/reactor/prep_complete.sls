
delete minion:
  runner.queue.delete:
    - queue: prep
    - items: {{ data['id'] }}


check:
  runner.check.queue:
    - queue: prep

