#!/usr/bin/python

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


#
# THIS IS NOT AN OSH COMMAND. 
# It is located here so that remoteinstall.py can easily access it for 
# remote installation
#


import sys
import os

OSH_VERSION = '1.0.3'
OSH = 'osh'

def os_system(command):
    os.system(command)

def os_chdir(dir):
    os.chdir(dir)

def os_mkdir(dir):
    os.mkdir(dir)

def args():
    args = sys.argv[1:]
    staging_dir = args[0]
    package_filename = args[1]
    install_dir = args[2]
    return staging_dir, package_filename, install_dir

def main():
    staging_dir, package_filename, install_dir = args()
    os_chdir(staging_dir)
    os_mkdir(OSH)
    os_chdir(OSH)
    os_system('tar mxzvf ../%s' % package_filename)
    os_chdir('..')
    os_system('rm -rf %s/%s' % (install_dir, OSH))
    os_system('mv %s %s' % (OSH, install_dir))
    os_chdir('..')
    os_system('rm -rf %s' % OSH)

if __name__ == '__main__':
    main()
