#!/bin/bash

if [ ! -f $1 ]; then
    echo "expected file to execute"
fi

LOGICAL_CORES=`lscpu | grep ^CPU.s.:  | sed -e "s/.*: *\([0-9]*\)/\1/g"`
TEST_SUITES=($($@ --gtest_list_tests | grep "^[^ ]" | sort))
NUM_OF_SUITES=$($@ --gtest_list_tests | grep "^[^ ]" | sort | wc -l)
NUM_OF_TESTS=$($@ --gtest_list_tests | grep "^ " | grep -v "^ *DISABLED" | wc -l)
if [ -z ${VERBOSE} ]; then
    VERBOSE=1
fi
if [ -z ${NUM_OF_SHARDS} ]; then
    NUM_OF_SHARDS=$LOGICAL_CORES
else
    LOGICAL_CORES=$NUM_OF_SHARDS
fi
if [ "${RUN_PER_SUITE}" == 1 ]; then
    NUM_OF_SHARDS=$NUM_OF_SUITES
fi

function execute_test()
{
    index=$1
    shift
    shards=$1
    shift
    tmpfile=$1
    shift
    COMMAND="$VALGRIND $VALGRIND_OPTS $@ $GTEST_OPTS"
    if [ ${VERBOSE} -ge 2 ]; then
        echo "executing $index shard (out of $shards) for command: 'GTEST_TOTAL_SHARDS=$shards GTEST_SHARD_INDEX=$index $COMMAND'" 1>&2
        GTEST_TOTAL_SHARDS=$shards GTEST_SHARD_INDEX=$index $COMMAND 1>&2
        OK=$?
    else
        GTEST_TOTAL_SHARDS=$shards GTEST_SHARD_INDEX=$index $COMMAND > $tmpfile
        OK=$?
    fi
    if [ ! "$OK" == "0" ]; then
        if [ ${VERBOSE} -lt 2 ]; then
            cat $tmpfile 1>&2
        fi
        echo "FAILED"
        if [ ${VERBOSE} -ge 1 ]; then
            echo -e "[ \e[31mFAILED\e[0m ] GTEST_SHARD_INDEX=$index GTEST_TOTAL_SHARDS=$shards $COMMAND" 1>&2
        fi
    else
        echo "OK"
        if [ ${VERBOSE} -ge 1 ]; then
            echo -e "[ \e[32mOK\e[0m ] GTEST_SHARD_INDEX=$index GTEST_TOTAL_SHARDS=$shards $COMMAND" 1>&2
        fi
    fi
}

function execute_shard()
{
    index=$1
    shift
    output_file=$1
    shift

    if [ ! -z ${VALGRIND} ]; then
        VALGRIND_OPTS="$VALGRIND_OPTS --xml=yes --xml-file=$1"
        shift
    fi
    if [ ! -z ${XML_OUTPUT} ]; then
        GTEST_OPTS="--gtest_output=xml:$1"
        shift
    fi

    COMMAND="$VALGRIND $VALGRIND_OPTS $@ $GTEST_OPTS"
    if [ "${RUN_PER_SUITE}" == 2 ]; then
        for i in `seq 0 $(($NUM_OF_SUITES-1))`; do
            execute_test $index $NUM_OF_SHARDS $output_file $@ --gtest_filter=${TEST_SUITES[$i]}*
        done
    elif [ "${RUN_PER_SUITE}" == 1 ]; then
        execute_test 0 1 $output_file $@ --gtest_filter=${TEST_SUITES[$index]}*
    else
        execute_test $index $NUM_OF_SHARDS $output_file $@
    fi
}

tmpfile_res=$(mktemp /tmp/parallet_gtest_executor.XXXXXX)

PGID=$(ps -o pgid= $$ | grep -o [0-9]*)
trap "echo 'KILLED' & kill -- -$PGID & rm -f $xmlOutList $valgrindXmlOutList $outputList" INT TERM
echo "There are $NUM_OF_TESTS all tests, they will be split into $NUM_OF_SHARDS shards"
valgrindXmlOutList=""
xmlOutList=""
outputList=""
for i in `seq 0 $(($NUM_OF_SHARDS-1))`; do
    outputFiles[$i]=$(mktemp /tmp/parallel_gtest_executor.out.XXXXXX)
    outputList="$outputList ${outputFiles[$i]}"
    if [ ! -z ${VALGRIND} ]; then
        tmpValgrindXmlOut[$i]=$(mktemp /tmp/parallel_gtest_executor.XXXXXX.valgrind.xml)
        valgrindXmlOutList="$valgrindXmlOutList ${tmpValgrindXmlOut[$i]}"
    fi
    if [ ! -z ${XML_OUTPUT} ]; then
        tmpXmlOut[$i]=$(mktemp /tmp/parallel_gtest_executor.XXXXXX.xml)
        xmlOutList="$xmlOutList ${tmpXmlOut[$i]}"
    fi
    execute_shard $i ${outputFiles[$i]} ${tmpValgrindXmlOut[$i]} ${tmpXmlOut[$i]} "$@" >> $tmpfile_res &
    if [ $(($((i+1)) % $LOGICAL_CORES)) -eq 0 ]; then
        wait
    fi
done

wait

if [ ! -z ${VALGRIND} ]; then
    echo "<valgrindoutput>" > valgrind.xml
    cat $valgrindXmlOutList | grep -v "<?xml version=.*?>" | grep -v "\(<\|<.\)valgrindoutput>" >> valgrind.xml
    echo "</valgrindoutput>" >> valgrind.xml
    RESULT=$?
    if [ ! "$RESULT" == "0" ]; then
        exit 10
    fi
fi
if [ ! -z ${XML_OUTPUT} ]; then
    cat $xmlOutList > $XML_OUTPUT
fi

OK_TESTS=`cat $tmpfile_res | grep "^OK$" | wc -l`
FAILED_TESTS=`cat $tmpfile_res | grep -v "^OK$" | wc -l`
TOTAL_TESTS=$(($OK_TESTS+$FAILED_TESTS))
echo "OK $OK_TESTS/$TOTAL_TESTS"
echo "FAILED $FAILED_TESTS/$TOTAL_TESTS"
rm $xmlOutList $valgrindXmlOutList $outputList $tmpfile_res
if [ $FAILED_TESTS -gt 0 ]; then
    exit 11
fi

