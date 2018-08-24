#!/usr/bin/env python3
#coding: utf-8
#

import signal
signal.signal(signal.SIGINT,signal.SIG_DFL)

_usage = ["python3 maf2tsv.py maf.maf"]
_sample = ["python3 maf2tsv maf.maf"]
_version = "Fri Aug 24 15:00:00 JST 2018"
_code = "transform from maf to tsv"

import sys
import os


###########################################
#メイン関数
def main(argv):

	argv = argv[1:]

	case = -1
	type = 0
	chr = 0
	build = 0
	with open(argv[0], encoding='utf-8') as f:
		for line in f:
			line = line.rstrip()
			if line.startswith("#"):
				continue
			list = line.split("\t")
			if case == -1:
				for cnt in range(len(list)):
					if list[cnt] == "Tumor_Sample_Barcode":
						case = cnt
					if list[cnt] == "Variant_Type":
						type = cnt
					if list[cnt] == "Chromosome":
						chr = cnt
					if list[cnt] == "NCBI_Build":
						build = cnt
				sys.stdout.write("Case_Id\tChr_Build\t" + line + "\n")
			else:
#				if list[type] == "SNP":
					clist = list[case].split("-")
					sys.stdout.write("-".join(clist[:3]) + "\t" + "http://identifiers.org/hco/" + list[chr][3:] + "#" + list[build] + "\t" + line + "\n")
	return 0

if __name__ == '__main__': sys.exit(main(sys.argv))

