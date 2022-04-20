#!/bin/bash

DIR=references

rm -rf $DIR
mkdir $DIR

for i in `cat ../examples/crossroads-by-name.json|python3 -c 'import sys, json; print(" ".join([k for k in json.load(sys.stdin)]))'`; do 
    echo "Processing $i crossroad"
    PYTHONPATH=$PWD/.. ../examples/get-crossroad-description.py --by-name $i --multiscale --to-json-all $DIR/$i-multiscale.json
done
