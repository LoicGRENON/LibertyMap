#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

APP_NAME        = u'LibertyMap'
APP_VERSION     = u'1.0'
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

def ensure_dir(f):
	d = os.path.dirname(f)
	if not os.path.exists(d):
		os.makedirs(d)
