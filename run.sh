#!/bin/bash

rm -f *.tmp.tsv
python3 maf2tsv.py $2 > $$.tmp.tsv
python3 simpleT2R.py $1 $$.tmp.tsv 
