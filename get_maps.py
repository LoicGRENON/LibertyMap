#!/usr/bin/python
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup	# For processing HTML
import re
import os
import sys
import urllib

def get_maps() :
	map_no = {'row_start':0, 'col_start':0, 'file':'Maps/nord_ouest.html'}
	map_ne = {'row_start':0, 'col_start':60, 'file':'Maps/nord_est.html'}
	map_so = {'row_start':50, 'col_start':0, 'file':'Maps/sud_ouest.html'}
	map_se = {'row_start':50, 'col_start':60, 'file':'Maps/sud_est.html'}	
	maps = [map_no, map_ne, map_so, map_se]

	time_pattern = "\([0-9]*,[0-9]*\) : ([0-9]*)min"
	time = None

	img_list = []

	grid = [[{'x_coord':col,'y_coord':row,'time':0, 'img':None, 'decor':None, 'is_passage':False} for col in range(121)] for row in range(139)]
	for carte in maps :
		print "Traitement du fichier %s" % str(carte['file'])

		file = open(carte['file'], "r")
		html = file.read()
		file.close()
		soup = BeautifulSoup(html)

		table = soup.find("table")

		y_coord = carte['row_start']
		for row in table.findAll("tr") :
			x_coord = carte['col_start']
			for col in row.findAll("td") :
				try :
					time = re.findall(time_pattern, col["title"])
				except KeyError :
					time = None
		
				if time != None and len(time) :
					time = time[0]
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
				else :
					is_passage = False

				try :
					#if grid[x_coord][y_coord] == {0, None} :
					grid[y_coord][x_coord] = {'x_coord':x_coord,'y_coord':y_coord,'time':str(time), 'img':str(img["src"]), 'decor':decor, 'is_passage':is_passage}

				except IndexError :
					print "Index Error : x_coord = %i, y_coord = %i" % (x_coord,y_coord)
					break
				x_coord += 1

			y_coord += 1

	# On vérifie qu'il n'y a pas de nouvelle image, dans le cas contraire, on la récupère
	error = 0
	for img in img_list :
		path = '/home/loic/Programmation/Calculateur Trajet/media' + img
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

if __name__ == '__main__' :
	get_maps()
