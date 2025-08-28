#!/bin/bash

MSG="test message"

COMMAND="echo "$MSG" | nc server 12345"

RESULT=$(docker run --rm --network tp0_testing_net alpine sh -c "$COMMAND")

if [ "$RESULT" = "$MSG" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
