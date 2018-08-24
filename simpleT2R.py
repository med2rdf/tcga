#!/usr/bin/env python3
#coding: utf-8
#
# simpleT2R:
#
# designed by Shinichiro Tago
# written by Shinichiro Tago
#
# The MIT License
# 
# Copyright (C) 2013 Fujitsu Laboratories Ltd.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import signal
signal.signal(signal.SIGINT,signal.SIG_DFL)

_base = "base"
_prefix = "prefix"
_name = "name"
_uri = "uri"
_text = "text"
_label = "label"
_labels = "labels"
_subject = "subject"
_class = "class"
_classes = "classes"
_property = "property"
_object = "object"
_literal = "literal"
_integer = "integer"
_number = "number"
labelMap = {}

_usage = ["simpleT2R configFile tsvFile"]
_sample = ["simpleT2R ClinicalSig.conf ClinicalSig.tsv"]
_version = "Tue Dec 26 15:00:00 JST 2017"
_code = "simple translate from tsv into RDF"

import sys
import os
import io
import re
import codecs
import json
import urllib.parse

def die(msg):
	sys.stderr.write( 'Error[' + " ".join(sys.argv) + '] : ' + msg.replace('\n',';') + "\n")
	sys.exit(1)

def warning(msg):
	sys.stderr.write( 'Warning[' + " ".join(sys.argv) + '] : ' + msg.replace('\n',';') + "\n")

def openReadFile(file_name):
	if file_name != "-":
		try: return open(file_name,'r',encoding='utf-8')
		except: die("ファイルを開けません。" + file_name)

	sys.stdin = io.TextIOWrapper(sys.stdin, encoding='utf-8')
	return sys.stdin.buffer

class InputFile:
	def __init__(self, file_name):
		self.handler = openReadFile(file_name)
		self.eof = False
		self.row = 0
	def __iter__(self):
		return self

	def __next__(self):
		data = self.handler.readline()
		self.row += 1
		if data == '':
			raise StopIteration
		return self.decode(data)

	def readline(self):
		data = self.handler.readline()
		self.row += 1
		return self.decode(data)

	def decode(self,data):
			return data


def openWriteFile(file_name):
	if file_name != "-":
		try:    return open(file_name,'w')
		except: die("ファイルの書き込み許可がありません。" + file_name)

	return sys.stdout


class OutputFile:
	def __init__(self,file_name,code=''):
		self.handler = openWriteFile(file_name)
		self.error = None
		self.code = code
		self.state = 0
		self.buf = ""
		self.once = 0

	def write(self,data):
		if self.error:
			return False
		try:
			self.handler.write(data)
		except:
			self.error = True
			return True
		try:
			self.handler.flush()
		except:
			self.error = True
			return True
		return None

	def out(self,data,stage):

		if self.state != 3 and stage <= self.state:
			self.buf = ""
			self.state = self.once

		if stage != 1:
			data = "\t" + data

		if self.state == 3:
			if stage == 1:
				data = "\t.\n" + data
			elif stage == 2:
				data = "\t;\n" + data
			else:
				data = "\t," + data

		self.buf += data
		
		if stage == 1:
			self.buf += "\n"
		elif stage == 3:
			self.write(self.buf)
			self.buf = ""
			self.once = 3

		self.state = stage
		return

	def finish(self):
		if self.once == 3:
			self.write("\t.\n")

	def close(self):
		if self.error:
			return False
		self.error = True
		self.handler.close()
		return True

def nop(str):
	return str

def lower(str):
	return str.lower()

def title(str):
	return str.title()

def getResource(config,list,func,row):
	obj = ""
	if _literal in config:
		literal = config.get(_literal,"")
		if literal in labelMap:
			obj = list[labelMap.get(literal)]
			if len(obj) == 0:
				return None
			obj = "".join(["\"",obj,"\""])
		else:
			obj = "".join(["\"",literal,"\""])
		return obj
	if _integer in config:
		integer = config.get(_integer,"")
		if integer in labelMap:
			obj = list[labelMap.get(integer)]
			if len(obj) == 0:
				return None
		else:
			obj = integer
		return obj

	if _name in config:
		obj = config.get(_name)
		return obj
	
	
	labels = []
	if _text in config:
		t = config.get(_text)
		labels.append(config.get(_text))
	for label in config.get(_labels,[]):
		# need error check
		t = list[labelMap.get(label)]
		if len(t) == 0:
			return None
		labels.append(func(t))
	if _label in config:
		# need error check
		t = list[labelMap.get(config.get(_label))]
		if len(t) == 0:
			return None
		labels.append(func(t))
	if config.get(_number,False):
		labels.append(str(row-1))
	obj += "_".join(labels)

	if len(obj) == 0:
		return None

	obj = urllib.parse.quote(obj)
	obj = obj.replace("%3A",":").replace("%23","#")
	if _prefix in config:
		obj = config.get(_prefix) + ":" + obj
	else:
		obj = "<"+obj+">"

	return obj


###########################################
#メイン関数
def main(argv):

	argv = argv[1:]

	config_file_name = argv[0]
	output_file_name = "-"
	if len(argv) >= 2:
		input_file_name = argv[1]
		if len(argv) >= 3:
			output_file_name = argv[2]
	else:
		input_file_name = "-"

	config_file = open(config_file_name, 'r')
	config = json.load(config_file)

	input_file = InputFile(input_file_name)
	output_file = OutputFile(output_file_name)

	if _base in config:
		output_file.write("\t".join(["@base",config[_base],".\n"]))

	if _prefix in config:
		prefixConfig = config[_prefix]
		for pC in prefixConfig:
			if _name not in pC:
				continue
			if _uri not in pC:
				continue
			output_file.write("\t".join(["@prefix",pC[_name]+":",pC[_uri],".\n"]))


	line = input_file.readline()
	col = 0
	line = line.rstrip()
	for label in line.split("\t"):
		labelMap[label] = col
		col += 1
	
	subjConfig = config[_subject]
	for line in input_file:
		line = line.rstrip()
		list = line.split("\t")
		while len(list) < col:
			list.append("")
		for subjC in subjConfig:
			subject = getResource(subjC, list, nop, input_file.row)
			if subject is None:
				continue
			output_file.out(subject,1)
			if _class in subjC:
				output_file.out("a",2)
				output_file.out(subjC[_class],3)
			if _classes in subjC:
				output_file.out("a",2)
				for cl in subjC[_classes]:
					output_file.out(cl,3)

			propConfig = subjC.get(_property,[])
			for propC in propConfig:
				prop = getResource(propC, list, lower, input_file.row)
				if prop is None:
					continue
				output_file.out(prop,2)

				objConfig = propC.get(_object,[])
				for objC in objConfig:
					object = getResource(objC, list, nop, input_file.row)
					if object is None:
						continue
					output_file.out(object,3)
	output_file.finish()

	return 0

if __name__ == '__main__': sys.exit(main(sys.argv))

