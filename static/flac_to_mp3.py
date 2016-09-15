#!/usr/bin/python --
# -*- coding: utf-8 -*-
import sys, os, re, subprocess

lame_opts = '--vbr-new -V 0 -q 0'

def get(meta, key):
	try:
		val = meta[key]
		val = re.sub(r'\'', r"'\''", val)
		return '\'%s\'' % val
	except KeyError:
		return '\'\''

for root, dirs, files in os.walk('.'):
	for file in files:
		if not re.match(r'.*\.flac$', file):
			continue
		
		path = os.path.join(root, file)
		path = re.sub(r'\'', r"'\''", path)
		# Get metadata.
		meta = {}
		cmd = 'metaflac --list \'%s\'' % path
		p = subprocess.Popen(cmd, shell = True, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
		(child_stdout, child_stderr) = (p.stdout, p.stderr)
		for c in child_stdout:
			m = re.match(r'.*comment\[\d+\]: (.*)=(.*)$', c)
			if m:
				meta [m.group(1).lower()] = m.group(2)
		# Run flac to mp3 conversion.
		cmd = 'flac -dc \'%s\' | lame %s --tt %s --tn %s --tg %s --ty %s --ta %s --tl %s --add-id3v2 - \'%s.mp3\'' % \
			(path, lame_opts, get(meta, 'title'), get(meta, 'tracknumber'), get(meta, 'genre'), get(meta, 'date'), get(meta, 'artist'), get(meta, 'album'), os.path.splitext(path)[0])
		print cmd
		res = os.system(cmd)
		if res == 0:
			print 'OK'
