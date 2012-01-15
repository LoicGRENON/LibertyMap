#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import logging
import copy

class Node :
	'''
	A class representing a tile of the course
	'''
	def __init__(self, x, y, nodeGoal=None, parent=None, is_start=False, is_end=False, g=0, h=0, f=0, walkable=True, passage=False, time=100, img_base=None, img_decor=None):
		self.x = x
		self.y = y
		self.parent = parent
		self.is_start = is_start
		self.is_end = is_end
		self.g = g
		self.h = h
		self.f = f
		self.walkable = walkable
		self.passage = passage
		self.time = time
		self.path_time = 0
		self.img_base = img_base
		self.img_decor = img_decor

		if self.time == 100 :
			self.walkable = False

		# Si le noeud courant est un changement de zone, alors le cout de cette case est nul
		if self.passage :
			self.time = 0
			self.walkable = True

		self.computeScore(nodeGoal)

	def computeScore(self, nodeGoal, time_func=None) :
		if self.parent :
			if hasattr(time_func, '__call__') :	# Si l'argument est bien une fonction
				self.g = self.parent.g + time_func(self.time)
				self.path_time = self.parent.path_time + time_func(self.time)
			else :
				self.g = self.parent.g + self.time
				self.path_time = self.parent.path_time + self.time

			if self.x == self.parent.x or self.y == self.parent.y :
				self.g += 10
			else :
				self.g += 14

			self.h = self.returnHscore(nodeGoal)
		else :
			self.g = 0
			if self.is_start :
				self.h = self.returnHscore(nodeGoal)
			else :
				self.h = 0

		self.f = self.g + self.h

	def returnGscore(self, time_func=None) :
		if self.parent :
			if hasattr(time_func, '__call__') :	# Si l'argument est bien une fonction
				g = self.parent.g + time_func(self.time)
			else :
				g = self.parent.g + self.time

			if self.x == self.parent.x or self.y == self.parent.y :
				g += 10
			else :
				g += 14
		else :
			g = 0

		return g

	def returnHscore(self, nodeGoal) :
		x = abs(self.x - nodeGoal.x)
		y = abs(self.y - nodeGoal.y)
		return max(x,y)

	def getNeighbours(self, graph, nodeGoal):
		'''
		This method check for node's orthogonal and diagonal contiguous nodes.
		It returns a list of contiguous nodes
		'''
		neighbours = set()

		max_x = len(graph[0])
		max_y = len(graph)

		northAmbit = 0 if self.y == 0 else self.y - 1
		southAmbit = self.y if self.y == max_y - 1 else self.y + 1
		westAmbit = 0 if self.x == 0 else self.x - 1
		eastAmbit = self.x if self.x == max_x - 1 else self.x + 1

		for i in xrange(northAmbit, southAmbit + 1) :
			for j in xrange(westAmbit, eastAmbit + 1) :
				if (i != self.y or j != self.x) :
					if graph[i][j].walkable :
						# Si la case voisine est un changement de zone, alors son coût est nul
						if graph[i][j].passage :
							graph[i][j].time = 0
						# Si le noeud courant est un changement de zone, alors le cout des cases voisines est nul
						if self.passage :
							if self.parent :
								if self.parent.x != graph[i][j].x or self.parent.y != graph[i][j].y :
									# On annule le coût des cases voisines aux changement de zone, sauf celle d'où on vient (le noeud parent)
									graph[i][j].time = 0
							else :	# Si la case de départ est un changement de zone ...
								graph[i][j].time = 0
						neighbours.add(graph[i][j])
		return neighbours


class PathFinder :

	def __init__(self, graph, x_start, y_start, x_end, y_end, time_func=None):
		self.graph = graph
		self.x_start = x_start
		self.y_start = y_start
		self.x_end = x_end
		self.y_end = y_end
		self.time_func = time_func

		self.openSet = set()
		self.closeSet = set()

		self.nodeGoal = graph[y_end][x_end]

		logging.basicConfig(
			filename='debug.log',
			filemode='w',
			level=logging.DEBUG,
			format='%(asctime)s %(levelname)s - %(message)s',
			datefmt='%d/%m/%Y %H:%M:%S',
			)

	def addToCloseSet(self, node):
		self.openSet.discard(node)
		self.closeSet.add(node)

	def addToOpenSet(self, node):
		#self.closeSet.discard(node)
		self.openSet.add(node)

	def getCurrentNode(self):
		return min(self.openSet, key=lambda node:node.f)

	def isOnCloseSet(self, node):
		if node in self.closeSet :
			return True
		else :
			return False

	def isOnOpenSet(self, node):
		if node in self.openSet :
			return True
		else :
			return False

	def findPath(self):
		path = []

		def retracePath(c):
			path.insert(0,c)
			if c.parent == None:
				return path
			retracePath(c.parent)

		# Si le noeud de départ ou d'arrivée ne peuvent pas être traversées, il n'y a pas de trajet possible
		if not self.graph[self.y_start][self.x_start].walkable or not self.graph[self.y_end][self.x_end].walkable :
			return path

		curNode = self.graph[self.y_start][self.x_start]
		self.addToOpenSet(curNode)
		while len(self.openSet) :
			# On va chercher le noeud avec le plus petit score F. Ça sera notre noeud courant
			curNode = self.getCurrentNode()
			if curNode.parent :
				logging.debug("Noeud courant : (%i, %i) - Parent : (%i, %i) - G = %i | H = %i | F = %i | Walkable : %s | Passage : %s", curNode.x, curNode.y, curNode.parent.x, curNode.parent.y, curNode.g, curNode.h, curNode.f, curNode.walkable, curNode.passage)
			else :
				logging.debug("Noeud courant : (%i, %i) - Parent : None     - G = %i | H = %i | F = %i | Walkable : %s | Passage : %s", curNode.x, curNode.y, curNode.g, curNode.h, curNode.f, curNode.walkable, curNode.passage)
			self.addToCloseSet(curNode)

			# Stopper la boucle si curNode est le noeud d'arrivée
			if curNode.is_end :
				logging.debug("Chemin trouvé ! Temps total du trajet : %i ", curNode.path_time)
				retracePath(curNode)
				break

			# On récupère les voisins du noeud courant
			neighbours = curNode.getNeighbours(self.graph, self.nodeGoal)
			for neighbour in neighbours :
				# Si le noeud est dans la liste fermée ou que c'est un obstacle => on l'ignore et on passe au suivant
				if (neighbour in self.closeSet) or not neighbour.walkable :
					continue

				if neighbour in self.openSet:
					newG = neighbour.returnGscore(self.time_func)
					#if curNode.g + neighbour.g < neighbour.g :
					if newG < neighbour.g :
						neighbour.parent = curNode
						neighbour.computeScore(self.nodeGoal, self.time_func)
						logging.debug("(%i,%i) - G : %i - H : %i - in openSet : Yes", neighbour.x, neighbour.y, neighbour.g, neighbour.h)
				else :
					neighbour.parent = curNode
					neighbour.computeScore(self.nodeGoal, self.time_func)
					logging.debug("(%i,%i) - G : %i - H : %i - in openSet : No", neighbour.x, neighbour.y, neighbour.g, neighbour.h)
					self.addToOpenSet(neighbour)
		
		return path
