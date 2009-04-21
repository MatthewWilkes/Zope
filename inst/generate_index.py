"""
Generate an index file based on the version.cfg file of Zope 2
in order to provide a version specific index page generated to be used
in combination with easy_install -i <some_url>
"""

import os
import sys
from xmlrpclib import Server
from ConfigParser import ConfigParser

CP = ConfigParser()
CP.read(['versions.cfg'])

server = Server('http://pypi.python.org/pypi')
links = list()

dirname = sys.argv[1]

for package in CP.options('versions'):
    version = CP.get('versions', package)
    print >>sys.stderr, 'Package %s==%s' % (package, version)
    dest_dir = os.path.join(dirname, package)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    index_html = os.path.join(dest_dir, 'index.html')

    fp = file(index_html, 'w')
    print >>fp, '<html><body>'
    for d in server.package_urls(package, version):
        link = '<a href="%s">%s</a>' % (d['url'], d['filename'])
        print >>fp, link
        print >>fp, '<br/>'
    print >>fp, '</body></html>'
    fp.close()
