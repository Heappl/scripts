#!/bin/bash
(find $1 -name "*.c" -or -name "*.cc" -or -name "*.cpp" -or -name "*.h" -or -name "*.hh" -or -name "*.hpp" | grep -v "\<test\>" | xargs cat ) | wc $2


