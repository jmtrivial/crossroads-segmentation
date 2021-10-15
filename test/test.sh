#!/bin/bash

REFDIR=references
TESTDIR=test

rm -rf $TESTDIR
mkdir $TESTDIR

NBERROR=0
NB=0
for i in `cat ../src/crossroads-by-name.json|python3 -c 'import sys, json; print(" ".join([k for k in json.load(sys.stdin)]))'`; do 
    echo "Processing $i crossroad"
    TESTFILE=$TESTDIR/$i-multiscale.json
    REFFILE=$REFDIR/$i-multiscale.json
    ../src/get-crossroad-description.py --by-name $i --multiscale --to-json-all $TESTFILE
    echo " comparison"
    DIFF=$(diff $TESTFILE $REFFILE) 
    if [ "$DIFF" != "" ]; then
        echo "/!\\ $i has been modified /!\\"
        NBERROR=$((NBERROR + 1))
    else
        echo " ok"
    fi
    NB=$((NB + 1))
done

echo ""
echo ""
echo "Conclusion: $NBERROR error(s) on $NB crossroads"
