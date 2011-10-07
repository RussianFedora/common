#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os, os.path
from urlparse import urlparse
import hashlib
import urllib

class RFRGetSources:
    debug_mode = 0

    def __init__(self):
        self.current_dir = os.curdir
        self.sources = {}
        self.has_error = False
        self.read_sources()

        self.user_script_name = os.path.join(self.current_dir, 'get_sources.sh')

    def check(self):
        self.debug("Begin check")
        if self.has_error:
            return False
        if len(self.sources.keys()) == 0:
            return True

        self.debug('check user script')
        if self.check_user_script():
            return self.run_user_script()
        else:
            return self.get_sources()

    def check_user_script(self):
        return os.path.exists(self.user_script_name)
    
    def run_user_script(self):
        if os.path.exists(self.user_script_name):
            self.debug("Try run %s" % ('/bin/sh %s' % self.user_script_name))
            try:
                os.system('/bin/sh %s' % self.user_script_name)
            except:
                self.debg('script fail')
                return False
            return True
        return False
    
    def read_sources(self):
        sources_f = os.path.join(self.current_dir, 'sources')
        if not os.path.exists(sources_f):
            self.has_error = True
            self.debug('File \'sources\' not found.')
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
            self.debug("Some spec-file: %s" % spec)
            params = {}
            spec_f = open(os.path.join(self.current_dir, spec), 'r')
            for line in spec_f:
                if (len(line) == 0) or (line[0] == '#'):
                    continue
                if (':' not in line) and ('define' not in line) and ('global' not in line):
                    continue
                
                if (':' in line):
                    try:
                        key, value = line.split()
                    except:
                        list_of_split = line.split()
                        if len(list_of_split) > 0:
                            key = list_of_split[0]
                            value = str(' ').join(list_of_split[1:])
                        else:
                            continue

                elif ('define' in line) or ('global' in line):
                    try:
                        define, key, value = line.split()
                    except:
                        continue
                    if define != '%define' and define != '%global':
                        continue
                params[key.replace(':', '').lower()] = value
            # fix inbound params
            for par in params.keys():
                if ('%' in params[par]) and ('?' not in params[par]):
                    raw_param = params[par]
                    try:
                        raw_param = raw_param.replace('%{','%(').replace('}',')s') % params
                    except:
                        continue
		    params[par] = raw_param
            for p in params.keys():
                if '://' in params[p] and ('source' in p.lower() or 'patch' in p.lower()) and p.lower() != 'url':
                    url_raw = params[p].replace('%{','%(').replace('}',')s') % params
                    self.debug(url_raw)
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

    def debug(self, msg, force = False):
        if (self.debug_mode != 0) or (force == True):
            print("rfr_get_source debug: %s" % msg)

if __name__ == '__main__':
    rfr = RFRGetSources()
    rfr.debug("Begin")
    
    try:
        check_status = rfr.check()
    except:
        rfr.debug("Error in download script. Please contact with author!", True)
        os._exit(1)

    if not check_status:
        rfr.debug("Abnormal exit", True)
        os._exit(1)
    rfr.debug("End. OK.")
    os._exit(0)

