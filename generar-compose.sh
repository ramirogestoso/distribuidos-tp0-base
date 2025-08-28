#!/bin/bash

# Function to display help message
function show_help {
  echo "Usage: $0 <output_filename> <number_of_clients>"
  echo
  echo "Generate a Docker Compose file with a server and specified number of clients."
  echo
  echo "Arguments:"
  echo "  <output_filename>     Path to the output Docker Compose file"
  echo "  <number_of_clients>   Number of client services to generate"
  echo
  echo "Example: $0 docker-compose.yml 3"
  exit 1
}

# Check if help is requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  show_help
fi


FILENAME=$1
CLIENTS_COUNT=$2

if ! [[ "$CLIENTS_COUNT" =~ ^[0-9][0-9]*$ ]]; then
  echo "Error: Number of clients must be a positive integer"
  show_help
fi

function generate_clients {
  local clients=""
  for i in $(seq 1 $1); do
      cat <<EOF
  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server

EOF
  done
}

cat > "$FILENAME" <<EOF
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net

$(generate_clients $CLIENTS_COUNT)

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF