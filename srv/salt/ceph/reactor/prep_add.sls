
add minion:
  runner.queue.insert:
    - queue: prep 
    - items: {{ data['id'] }}

