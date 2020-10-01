#!/bin/bash
2to3 -w $(find ./ -name '*.py')
autoflake -i --expand-star-imports --remove-all-unused-imports --remove-duplicate-keys \
    $(find ./ -name '*.py' ! -name '*_pb2.py' ! -path '*/migrations/*')
autopep8 -i -a -a -a -a --experimental -j 8 --max-line-length 120 \
    $(find ./ -name '*.py' ! -name '*_pb2.py' ! -path '*/migrations/*')
isort -w 121 $(find ./ -name '*.py' ! -name '*_pb2.py' ! -path '*/migrations/*')
