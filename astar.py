#!/usr/bin/python
# -*- coding: utf-8 -*-

import heapq

class Node :
	'''
	A class representing a tile of the course
	'''
	def __init__(self, x, y, parent=None, g=0, h=0, f=0, walkable=True, passage=False):
		self.x = x
		self.y = y
		self.parent = parent
		self.g = g
		self.h = h
		self.f = f
		self.walkable = walkable
		self.passage = passage
		self.visited = False
		self.closed = False


class PathFinder :

	def __init__(self, graph, x_start, y_start, x_end, y_end):
		self.graph = graph
		self.x_start = x_start
		self.y_start = y_start
		self.x_end = x_end
		self.y_end = y_end

	def getNodeFromGraph(self, abscisse, ordonnee):
		x_coord = int(self.graph[ordonnee][abscisse]['x_coord'])
		y_coord = int(self.graph[ordonnee][abscisse]['y_coord'])

		node = Node(x_coord, y_coord)
		node.g = int(self.graph[ordonnee][abscisse]['time'])

		if node.g == 100 :
			node.walkable = False

		node.passage = self.graph[ordonnee][abscisse]['is_passage']
		if node.passage :
			node.g = 0

		return node

	def getNeighbours(self, node):
		'''
		This method check for current node's orthogonal and diagonal contiguous nodes.
		It returns a list of contiguous nodes
		'''
		neighbours = []
		max_x = len(self.graph[0])
		max_y = len(self.graph)

		neighbours_up = node.y - 1	# Ordonnée de la ligne au dessus du noeud
		neighbours_down = node.y + 1	# Ordonnée de la ligne en dessous du noeud
		neighbours_left = node.x - 1	# Abscisse de la colonne à gauche du noeud
		neighbours_right = node.x + 1	# Abscisse de la colonne à droite du noeud

		if neighbours_up > -1 :
			# La ligne du dessus existe alors il y a au moins 2 voisins au dessus du noeud
			if neighbours_left > -1 :
				# On ajoute le noeud en haut gauche du noeud courant
				neighbour = self.getNodeFromGraph(neighbours_left, neighbours_up)
				neighbour.parent = node
				neighbours.append(neighbour)
			# On ajoute le noeud au dessus du noeud courant
			neighbour = self.getNodeFromGraph(node.x, neighbours_up)
			neighbour.parent = node
			neighbours.append(neighbour)
			if neighbours_right < max_x :
				# On ajoute le noeud en haut droit du noeud courant
				neighbour = self.getNodeFromGraph(neighbours_right, neighbours_up)
				neighbour.parent = node
				neighbours.append(neighbour)
		
		if neighbours_right < max_x :
			# La colonne de droite existe alors il y a au moins 2 voisins à droite du noeud
			# On ajoute le noeud à droite du noeud courant
			neighbour = self.getNodeFromGraph(neighbours_right, node.y)
			neighbour.parent = node
			neighbours.append(neighbour)

		if neighbours_down < max_y :
			# La ligne du dessous existe alors il y a au moins 2 voisins en dessous du noeud
			if neighbours_right < max_x :
				# On ajoute le noeud en bas droit du noeud courant
				neighbour = self.getNodeFromGraph(neighbours_right, neighbours_down)
				neighbour.parent = node
				neighbours.append(neighbour)
			# On ajoute le noeud en dessous du noeud courant
			neighbour = self.getNodeFromGraph(node.x, neighbours_down)
			neighbour.parent = node
			neighbours.append(neighbour)
			if neighbours_left > -1 :
				# On ajoute le noeud en bas gauche du noeud courant
				neighbour = self.getNodeFromGraph(neighbours_left, neighbours_down)
				neighbour.parent = node
				neighbours.append(neighbour)

		if neighbours_left > -1 :
			# La colonne de gauche existe alors il y a au moins 2 voisins à gauche du noeud
			# On ajoute le noeud à gauche du noeud courant
			neighbour = self.getNodeFromGraph(neighbours_left, node.y)
			neighbour.parent = node
			neighbours.append(neighbour)

		return neighbours

	def findPath(self):
		path = []

		def retracePath(c):
			path.insert(0,c)
			if c.parent == None:
				return path
			retracePath(c.parent)

		curNode = self.getNodeFromGraph(self.x_start, self.y_start)
		openList = [(-1, curNode)]
		heapq.heapify(openList)

		while openList :
			# On va chercher le noeud avec le plus petit score F. Ça sera notre noeud courant
			score, curNode = heapq.heappop(openList)
			print "Noeud courant : (%i, %i) - G = %i | H = %i | F = %i | Walkable : %s | Passage : %s" % (curNode.x, curNode.y, curNode.g, curNode.h, curNode.f, curNode.walkable, curNode.passage)

			curNode.closed = True

			# Stopper la boucle si curNode est le noeud d'arrivée
			if curNode.x == self.x_end and curNode.y == self.y_end :
				print "Chemin trouvé !"
				retracePath(curNode)
				break

			# On récupère les voisins du noeud courant
			neighbours = self.getNeighbours(curNode)
			min_cost = min(neighbours, key=lambda node:node.g)
			for neighbour in neighbours :
				# Si le noeud est dans la liste fermée ou que c'est un obstacle => on l'ignore et on passe au suivant
				if neighbour.closed or not neighbour.walkable :
					continue

				# Si le noeud parent est un changement de zone, alors le cout de la case courante est nul
				if neighbour.parent.passage :
					neighbour.g = 0

				newG = neighbour.parent.g + neighbour.g
				newH = abs(self.x_end - neighbour.x) + abs(self.y_end - neighbour.y)
				if min_cost.g :
					newH *= min_cost.g
				newF = newG + newH

				if neighbour.visited :
					if newG < neighbour.g :
						neighbour.parent = curNode
						neighbour.g = newG
						neighbour.h = newH
						neighbour.f = newF
				else :
					neighbour.parent = curNode
					print "(%i,%i) - G : %i - H : %i" % (neighbour.x, neighbour.y, newG, newH)
					neighbour.g = newG
					neighbour.h = newH
					neighbour.f = newF
					heapq.heappush(openList, (neighbour.f, neighbour))
					neighbour.visited = True
		
		return path
