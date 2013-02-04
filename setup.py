# osh
# Copyright (C) Jack Orenstein <jao@geophile.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from distutils.core import setup
import os
import os.path

VERSION = '1.0.3'

def files(dir):
    output = []
    for path, subdirs, files in os.walk(dir):
        for file in files:
            output.append(os.path.join(path, file))
        break
    return output

doc = files('doc')
doc_web = files('doc/web')
doc_web_ref = files('doc/web/ref')
doc_web_userguide = files('doc/web/userguide')
scripts = files('scripts')
test = files('test')

setup(
    name = 'osh',
    version = VERSION,
    author = 'Jack Orenstein',
    author_email = 'jao@geophile.com',
    maintainer = 'Jack Orenstein',
    maintainer_email = 'jao@geophile.com',
    url = 'http://geophile.com/osh',
    license = 'GPL',
    description = 'object-oriented shell extensions',
    long_description = 'Command-line and API toolkit combining cluster access, database access, and data slicing and dicing.',
    keywords = 'python, command-line, API, cluster, database',
    platforms = 'Linux, OSX',
    download_url = 'http://geophile.com/osh/osh-%s.tar.gz' % VERSION,
    package_dir = {'': '.'},
    packages = ['osh',
                'osh.command',
                'osh.command.sqladapter',
                'osh.external',
                'osh.external.tpg'],
    data_files = [('/usr/bin', ['bin/osh', 'bin/remoteosh']),
                  ('/usr/share/osh/scripts', scripts),
                  ('/usr/share/osh/test', test),
                  ('/usr/share/doc/osh', doc),
                  ('/usr/share/doc/osh/web', doc_web),
                  ('/usr/share/doc/osh/web/ref', doc_web_ref),
                  ('/usr/share/doc/osh/web/userguide', doc_web_userguide)]
    )
