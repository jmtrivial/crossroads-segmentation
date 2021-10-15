#!/bin/bash

DIR=references

rm -rf $DIR
mkdir $DIR

for i in `cat ../src/crossroads-by-name.json|python3 -c 'import sys, json; print(" ".join([k for k in json.load(sys.stdin)]))'`; do 
    echo "Processing $i crossroad"
    ../src/get-crossroad-description.py --by-name $i --multiscale --to-json-all $DIR/$i-multiscale.json
done
