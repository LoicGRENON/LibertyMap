#!/usr/bin/python
# -*- coding: utf-8 -*-

from lxml import etree	# For XML parsing
import os
import sys
import urllib, urllib2
import astar
from common import ensure_dir, LM_CACHE_PATH

def check_images(img_list) :
	new_img = set()
	for img in img_list :
		path = LM_CACHE_PATH + os.sep + 'media' + os.sep + img
		if not os.access(path, os.F_OK):
			new_img.add(img)

	return new_img

def download_images(img_list) :
	for img in img_list :
		if os.name == "nt" :
			path = LM_CACHE_PATH + os.sep + 'media' + os.sep + os.sep.join(img.split('/'))
		else :
			path = LM_CACHE_PATH + os.sep + 'media' + os.sep + img
		img_path = 'http://libertyisland.johndegey.org/' + img
		print "Récupération de l'image '%s' vers %s" % (img_path, path)
		try :
			ensure_dir(path)
			urllib.urlretrieve(img_path, path)
			print "Succès"
		except :
			(exctype, value, traceback) = sys.exc_info()
			print "Erreur - %s : %s" % (exctype, value)

def download_image(img) :
	if os.name == "nt" :
		path = LM_CACHE_PATH + os.sep + 'media' + os.sep + os.sep.join(img.split('/'))
	else :
		path = LM_CACHE_PATH + os.sep + 'media' + os.sep + img
	img_path = 'http://libertyisland.johndegey.org/' + img
	try :
		ensure_dir(path)
		urllib.urlretrieve(img_path, path)
		return True
	except :
		return False

def get_map(xml_file) :
	# On crée la matrice qui contiendra les infos de la carte
	grid = [[astar.Node(col, row) for col in range(121)] for row in range(139)]
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

