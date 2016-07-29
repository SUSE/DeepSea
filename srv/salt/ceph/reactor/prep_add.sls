
add minion:
  runner.filequeue.enqueue:
    - kwargs:
        queue: prep 
        item: {{ data['id'] }}

