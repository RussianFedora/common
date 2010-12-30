#!/usr/bin/env python

import sys
import os, os.path
from urlparse import urlparse
import hashlib
import urllib

class RFRGetSources:
	def __init__(self):
		self.current_dir = os.curdir
		self.sources = {}
		self.has_error = False
		self.read_sources()

		self.user_script_name = os.path.join(self.current_dir, 'get_sources.sh')

	def check(self):
		print("Begin check")
		if self.has_error:
			return False
		if len(self.sources.keys()) == 0:
			return True

		print('check user script')
		if self.check_user_script():
			return self.run_user_script()
		else:
			return self.get_sources()

	def check_user_script(self):
		return os.path.exists(self.user_script_name)
	
	def run_user_script(self):
		if os.path.exists(self.user_script_name):
			print "Try run %s" % ('/bin/sh %s' % self.user_script_name)
			try:
				os.system('/bin/sh %s' % self.user_script_name)
			except:
				print('script fail')
				return False
			return True
		return False
	
	def read_sources(self):
		sources_f = os.path.join(self.current_dir, 'sources')
		if not os.path.exists(sources_f):
			self.has_error = True
			print('File \'sources\' not found.')
		try:
			s = open(sources_f, 'r')
		except:
			self.has_error = True
			return
		for l in s:
			checksum,filename = l.split()
			self.sources[filename] = checksum
		s.close()
	
	def _filename_from_url(self, url):
		u = urlparse(url)
		if len(u.scheme) == 0 or len(u.netloc) == 0:
			return ''

		path = u.path.split('/')
		return path[-1:][0]

	def get_sources(self):
		sources_list = {}
		for spec in os.listdir(self.current_dir):
			if 'spec' not in spec: # == '.' or spec == '..':
				continue
			print "Some spec-file: %s" % spec
			params = {}
			spec_f = open(os.path.join(self.current_dir, spec), 'r')
			for line in spec_f:
				if ':' not in line:
					continue
				try:
					key, value = line.split()
				except:
					continue
				params[key.replace(':', '').lower()] = value
			for p in params.keys():
				if '://' in params[p] and ('source' in p.lower() or 'patch' in p.lower()) and p.lower() != 'url':
					url_raw = params[p].replace('%{','%(').replace('}',')s') % params
					#print url_raw
					u = urllib.urlopen(url_raw)
					filename = self._filename_from_url(u.url)
					if len(filename) != 0:
						sources_list[u.url] = filename
						data = u.read()
						f = open(filename, 'wb')
						f.write(data)
						f.close()

		
		res = self.download_files(sources_list)
		return res

	def md5_for_file(self, f, block_size=2**20):
		md5 = hashlib.md5()
		with open(f,'rb') as f:
			for chunk in iter(lambda: f.read(8192), ''):
				md5.update(chunk)
		return md5.digest()

	def download_files(self, src_dict):
		res = True
		for url in src_dict.keys():
			fn = src_dict[url]
			d_file = os.path.join(self.current_dir, fn)
			if os.path.exists(d_file) and self.sources.has_key(fn):
				check_sum_s = self.sources[fn]
				check_sum_f = self.md5_for_file(d_file)
				res = res and check_sum_s != check_sum_f
		return res


if __name__ == '__main__':
	rfr = RFRGetSources()
	print("Begin")
	if not rfr.check():
		print "Abnormal exit"
		os._exit(1)
	os._exit(0)

