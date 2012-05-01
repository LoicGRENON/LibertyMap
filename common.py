#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

APP_NAME        = u'LibertyMap'
APP_VERSION     = u'1.0.2'
# List of authors
APP_AUTHORS     = [u'Loïc GRENON <difool@tuxfamily.org>']
APP_YEAR        = u'2012'
APP_WEBSITE     = u'http://libertymap.difoolou.net'
APP_COPYRIGHT   = u"Copyright © %s Loïc GRENON" % (APP_YEAR)
# XXX: Put description here
APP_DESCRIPTION = u"""LibertyMap est un calculateur de trajet pour le jeu de rôle en ligne Pirates-Caraïbes (http://www.pirates-caraibes.com)"""

# license text of this application
APP_LICENSE     = u"""
LibertyMap est un logiciel libre ; vous pouvez le redistribuer et/ou
le modifier selon les termes de la Licence Publique Générale GNU
publiée par la Free Software Foundation ; soit la version 3 de la
license, soit (à votre discrétion) toute version ultérieure.

LibertyMap est distribué dans l'espoir qu'il puisse vous être utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie de VALEUR MARCHANDE
ou d'ADÉQUATION À UN BESOIN PARTICULIER. Consultez la Licence Publique
Générale GNU pour plus de détails.

Vous devez avoir reçu une copie de la Licence Publique Générale GNU
en même temps que LibertyMap ; si ce n'est pas le cas, écrivez à la
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301, États-Unis.
"""
APP_ICON = "/usr/share/pixmaps/libertymap.png"
if not os.access(APP_ICON,os.F_OK) :
    APP_ICON = "pixmaps/libertymap.png"
if not os.access(APP_ICON,os.F_OK) :
    APP_ICON = "../pixmaps/libertymap.png"


LM_DIRNAME = 'LibertyMap'
# Emplacements dépendants de l'OS
if 'APPDATA' in os.environ:
    try :
        from win32com.shell import shellcon, shell #@UnresolvedImport
        appdata_path = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
    except :
        appdata_path = os.environ['APPDATA']
    LM_CONFIG_PATH = os.path.join(appdata_path, LM_DIRNAME)
    LM_CACHE_PATH = os.path.join(LM_CONFIG_PATH, 'cache')
elif 'XDG_CONFIG_HOME' in os.environ:
    LM_CONFIG_PATH = os.path.join(os.environ['XDG_CONFIG_HOME'], LM_DIRNAME)
    LM_CACHE_PATH = os.path.join(os.environ['XDG_CACHE_HOME'], LM_DIRNAME)
else:
    LM_CONFIG_PATH = os.path.join(os.environ['HOME'], '.config', LM_DIRNAME)
    LM_CACHE_PATH = os.path.join(os.environ['HOME'], '.cache', LM_DIRNAME)

# Autres emplacements
LM_CONF = os.path.join(LM_CONFIG_PATH, 'LibertyMap.conf')
LM_MAP = os.path.join(LM_CACHE_PATH, 'map.xml.gz')
LM_LOG = os.path.join(LM_CONFIG_PATH, 'LibertyMap.log')

# Detect if we're running on Windows
win32 = sys.platform.startswith("win")
# Detect if we're running a packed exe created with py2exe
py2exe = False
if win32 and hasattr(sys, 'frozen'):
    py2exe = True

if win32 and py2exe:
    LM_ERROR_LOG = os.path.join(LM_CONFIG_PATH, 'LibertyMap_error.log')
    try:
        sys.stdout = open(LM_ERROR_LOG, "w")
    except:
        print('Failed to close stdout (not so bad if you are using PyInstaller)')
    try:
        sys.stderr = open(LM_ERROR_LOG, "w")
    except:
        print('Failed to close stderr (not so bad if you are using PyInstaller)')

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
