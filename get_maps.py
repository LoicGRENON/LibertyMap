#!/usr/bin/python
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup	# For processing HTML
import re
import os
import sys
import cookielib, urllib, urllib2
import astar
from gui import LM_CACHE_PATH

def get_maps(login, password) :
	if login == None or login == '' or password == None or password == '' :
		print "Identifiants invalides"
		return ''

	map_no = {'row_start':0, 'col_start':0, 'map_id':'33', 'name':'Nord-Ouest'}
	map_ne = {'row_start':0, 'col_start':60, 'map_id':'34', 'name':'Nord-Est'}
	map_so = {'row_start':50, 'col_start':0, 'map_id':'35', 'name':'Sud-Ouest'}
	map_se = {'row_start':50, 'col_start':60, 'map_id':'36', 'name':'Sud-Est'}
	maps = [map_no, map_ne, map_so, map_se]

	time_pattern = "\([0-9]*,[0-9]*\) : ([0-9]*)min"
	time = None

	img_list = []

	# On crée la matrice qui contiendra les infos de la carte
	grid = [[astar.Node(col, row) for col in range(121)] for row in range(139)]

	# On active le support des cookies pour urllib2
	cookie_jar = cookielib.CookieJar()
	cookie_handler = urllib2.HTTPCookieProcessor(cookie_jar)
	urlOpener = urllib2.build_opener(cookie_handler)
	urllib2.install_opener(urlOpener)

	# On s'identifie sur le site
	print "Identification sur LibertyIsland" 
	params = urllib.urlencode({"user": login, "pwd": password}) 
	request = urllib2.Request("http://libertyisland.johndegey.org/index.php", params)
	urlOpener.open(request)

	for carte in maps :
		print "Récupération de la carte %s" % str(carte['name'])
		params = urllib.urlencode({"action": "showMap", "ajaxcall": "1", "anglais": "off", "espagnol": "off", "francais": "off", "hollandais": "off", "grillage": "off", "pirates": "off", "passage": "on", "pnj": "off", "pnjFixe": "off", "pnjPassif": "off", "pos": "", "selmap": "", "map": carte['map_id']})
		request = urllib2.Request("http://libertyisland.johndegey.org//restricted/zones.php", params)
		url = urlOpener.open(request)
		html = url.read()

		print "Traitement de la carte %s" % str(carte['name'])

		soup = BeautifulSoup(html)

		table = soup.find("table", {"class" : "cadre map"})

		y_coord = carte['row_start']
		for row in table.findAll("tr") :
			x_coord = carte['col_start']
			for col in row.findAll("td") :
				try :
					time = re.findall(time_pattern, col["title"])
				except KeyError :
					time = None
		
				if time != None and len(time) :
					time = int(time[0])
				else :
					time = 100
		
				for img in col.findAll("img", recursive=False) :
					if img["src"] not in img_list :
						img_list.append(str(img["src"]))

				decor = col.find("div", {"class" : "decor ac"})
				if decor != None :
					decor_img = decor.find("img")
					if decor_img["src"] not in img_list :
						img_list.append(str(decor_img["src"]))
					decor = str(decor_img["src"])

				if col.find("div", {"class" : "passage"}) != None :
					is_passage = True
					time = 0
				else :
					is_passage = False

				try :
					grid[y_coord][x_coord] = astar.Node(x_coord, y_coord, time = time, img_base = str(img["src"]), img_decor = decor, passage = is_passage)
				except IndexError :
					print "Index Error : x_coord = %i, y_coord = %i" % (x_coord,y_coord)
					break

				x_coord += 1
			y_coord += 1

	# On vérifie qu'il n'y a pas de nouvelle image, dans le cas contraire, on la récupère
	error = 0
	for img in img_list :
		path = LM_CACHE_PATH + '/media' + img
		if not os.access(path, os.F_OK):
			splited_path = os.path.split(path)
			if not os.access(splited_path[0], os.F_OK) :
				os.makedirs(splited_path[0])
			img_path = 'http://libertyisland.johndegey.org' + img
			print "Récupération de l'image '%s' vers %s" % (img_path, path)
			try :
				urllib.urlretrieve(img_path, path)
				print "Succès"
			except :
				error = 1
				print "Erreur"

	if error :
		print "Il y eu au moins une erreur."

	return grid
