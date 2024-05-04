#!/bin/bash

function engine {
  export PYTHONPATH=$(pwd)
  exec python app/engine/engine.py
}

function message_check_engine {
  export PYTHONPATH=$(pwd)
  exec python app/engine/message_check_engine.py
}

function nx_message_check_engine {
  export PYTHONPATH=$(pwd)
  exec python app/engine/nx_message_check_engine.py
}

function cm_message_check_engine {
  export PYTHONPATH=$(pwd)
  exec python app/engine/cm_message_check_engine.py
}

function generate_address_engine {
  export PYTHONPATH=$(pwd)
  exec python app/engine/generate_address_engine.py
}

function message_engine {
  export PYTHONPATH=$(pwd)
  exec python app/engine/message_engine.py
}

function message_timing_engine {
  export PYTHONPATH=$(pwd)
  exec python app/engine/message_timing_engine.py
}

function api_server {
    exec  uvicorn run:api --host='0.0.0.0' \
            --port=80  \
            --workers=2   \
            --log-config="logging_config.ini"
}

$1
