#!/usr/bin/python
# -*- coding: utf-8 -*-

from lxml import etree	# For XML parsing
import re
import os
import sys
import cookielib, urllib, urllib2
import astar
from gui import LM_CACHE_PATH

def check_images(img_list) :
	new_img = set()
	for img in img_list :
		path = LM_CACHE_PATH + '/media' + img
		if not os.access(path, os.F_OK):
			new_img.add(img)

	return new_img

def download_images(img_list) :
	for img in img_list :
		path = LM_CACHE_PATH + '/media' + img
		img_path = 'http://libertyisland.johndegey.org' + img
		print "Récupération de l'image '%s' vers %s" % (img_path, path)
		try :
			urllib.urlretrieve(img_path, path)
			print "Succès"
		except :
			print "Erreur"

def get_map(xml_file) :
	# On crée la matrice qui contiendra les infos de la carte
	grid = [[astar.Node(col, row) for col in range(121)] for row in range(139)]
	img_list = set()

	#etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False, no_network=False))
	tree = etree.parse(xml_file)
	root = tree.getroot()
	for element in root.iter("Tile"):
		x = int(element.attrib.get('x'))
		y = int(element.attrib.get('y'))
		time = element.attrib.get('time')
		if time != None :
			grid[y][x].time = time
		for child in element.iterchildren() :
			if child.tag == "Img" :
				img_src = child.attrib.get('src')
				grid[y][x].img_base = img_src
				img_list.add(img_src)
			elif child.tag == "Decor" :
				decor_src = child.attrib.get('src')
				grid[y][x].img_decor = decor_src
				img_list.add(decor_src)
			elif child.tag == "is_passage" :
				grid[y][x].passage = True

	return (grid, img_list)

