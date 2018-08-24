#!/bin/bash


python3 maf2tsv.py $1 > $$.tmp.tsv
python3 simpleT2R.py mutation.conf $$.tmp.tsv > $2
