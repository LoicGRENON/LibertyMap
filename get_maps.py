#!/usr/bin/python
# -*- coding: utf-8 -*-

from lxml import etree	# For XML parsing
import os
import sys
import urllib2
import urllib
import urlparse
import astar
import shutil
import gtk
from common import ensure_dir, LM_CACHE_PATH

def check_images(img_list) :
	new_img = set()
	for img in img_list :
		path = LM_CACHE_PATH + os.sep + 'media' + os.sep + img
		if not os.access(path, os.F_OK):
			if os.name == "nt" :
				# On remplace les \ du chemin windows par des / pour les URLs ...
				img = '/'.join(img.split('\\'))
			new_img.add(img)

	return new_img

def download_images(img_list) :
	for img in img_list :
		if os.name == "nt" :
			path = LM_CACHE_PATH + os.sep + 'media' + os.sep + os.sep.join(img.split('/'))
		else :
			path = LM_CACHE_PATH + os.sep + 'media' + os.sep + img
		img_path = 'http://www.pirates-caraibes.com/' + img
		print "Récupération de l'image '%s' vers %s" % (img_path, path)
		try :
			ensure_dir(path)
			try :
				src = urllib2.urlopen(img_path)
			except urllib2.HTTPError :
				pass
			else :
				dst = open(path, 'wb')
				shutil.copyfileobj(src, dst)
			print "Succès"
		except :
			(exctype, value, traceback) = sys.exc_info()
			print "Erreur - %s : %s" % (exctype, value)

def download_image(img, window=None) :
	if os.name == "nt" :
		path = LM_CACHE_PATH + os.sep + 'media' + os.sep + os.sep.join(img.split('/'))
	else :
		path = LM_CACHE_PATH + os.sep + 'media' + os.sep + img
	img_path = 'http://www.pirates-caraibes.com/' + img
	try :
		ensure_dir(path)
		try :
			src = urllib2.urlopen(url_fix(img_path))
		except urllib2.HTTPError :
			return False
		else :
			dst = open(path, 'wb')
			shutil.copyfileobj(src, dst)
		return True
	except :
		return False

def get_map(xml_file) :
	# On crée la matrice qui contiendra les infos de la carte
	grid = [[astar.Node(col, row) for col in range(190)] for row in range(150)]
	img_list = set()

	tree = etree.parse(xml_file)
	root = tree.getroot()
	for element in root.iter("Tile"):
		x = int(element.attrib.get('x'))
		y = int(element.attrib.get('y'))
		time = element.attrib.get('time')
		img_base = None
		img_decor = None
		img_pnj = None
		pnj_name = None
		passage = False
		passage_name = None

		if time == None :
			time = 100
		for child in element.iterchildren() :
			if child.tag == "Img" :
				img_src = child.attrib.get('src')
				img_base = os.sep.join(img_src.split('/'))
				img_list.add(img_src)
			elif child.tag == "Decor" :
				decor_src = child.attrib.get('src')
				img_decor = os.sep.join(decor_src.split('/'))
				img_list.add(decor_src)
			elif child.tag == "PNJ" :
				img_pnj_src = child.attrib.get('src')
				img_pnj = os.sep.join(img_pnj_src.split('/'))
				img_list.add(img_pnj)
				pnj_name = child.attrib.get('name')
			elif child.tag == "is_passage" :
				passage = True
				passage_name = child.attrib.get('name')
			
		grid[y][x] = astar.Node(x, y, time=int(time), img_base = img_base, img_decor = img_decor, img_pnj = img_pnj, pnj_name = pnj_name, passage = passage, passage_name = passage_name)

	return (grid, img_list)

def url_fix(s, charset='utf-8'):
	# http://stackoverflow.com/questions/120951/how-can-i-normalize-a-url-in-python
	"""Sometimes you get an URL by a user that just isn't a real
	URL because it contains unsafe characters like ' ' and so on.  This
	function can fix some of the problems in a similar way browsers
	handle data entered by the user:

	>>> url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
	'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'

	:param charset: The target charset for the URL if the url was
	                given as unicode string.
	"""
	if isinstance(s, unicode):
		s = s.encode(charset, 'ignore')
	scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
	path = urllib.quote(path, '/%')
	qs = urllib.quote_plus(qs, ':&=')
	return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))