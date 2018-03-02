#!/bin/sh
# Find actual path form which this script is launched
MY_PATH="`dirname \"$0\"`"
cd "$MY_PATH"

# Rewrite args
givenargs=""
for ARG in $*
do
        givenargs=${givenargs}" "$ARG
done

# Launch pyDarts with args
./pydarts.py $givenargs
