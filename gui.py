#!/usr/bin/python
# -*- coding: utf-8 -*-

# Gtk
import gtk

import thread

import get_maps

import time

class MainInterface :
	window, menu, statusBar = None, None, None

	def __init__(self) :
		print 'Initialisation de la fenêtre principale...'
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.connect("destroy", self.quit)
		self.window.set_title('Calculateur de trajet')

		vbox = gtk.VBox(False, True)
		self.window.add(vbox)

		# Barre de menu
		self.menu = MenuInterface(self)
		vbox.pack_start(self.menu.menu_bar, False, True)

		# Grille
		self.grid = GridInterface(self)
		self.grid.iconview.connect("item-activated", self.onActiveItem)
		self.grid.iconview.connect("selection-changed", self.onSelectionChange)
		vbox.pack_start(self.grid.gridBox, True, True)

		# Barre d'état
		self.statusBar = StatusBarInterface(self)
		vbox.pack_start(self.statusBar.status_bar, False, False, 0)

		self.window.show_all()

		thread.start_new_thread(self.ShowMap, ())

		gtk.gdk.threads_init()
		gtk.gdk.threads_enter()
		gtk.main()
		gtk.gdk.threads_leave()

	def quit(self, widget, data=None) :
		gtk.main_quit()

	def onActiveItem(self, widget, path) :
		self.statusBar.addText(str(path[0]))

	def onSelectionChange(self, widget)
		# Griser la case sélectionnée et dégriser celle qui est déselectionnée
		pass

	def ShowMap(self) :
		start_time = time.time()
		map_info = get_maps.get_maps()
		get_map_time = time.time() - start_time
		print "Durée de récupération des cartes : %f" % get_map_time

		start_time = time.time()
		i = 0
		for row in map_info :
			j = 0
			for col in row :
				gtk.gdk.threads_enter()
				if col['img'] != None :
					pixbuf = gtk.gdk.pixbuf_new_from_file("/home/loic/Programmation/Calculateur Trajet/media" + col['img'])
				else :
					pixbuf = gtk.gdk.pixbuf_new_from_file("/home/loic/Programmation/Calculateur Trajet/media/images/carregris.gif")

				# S'il y a un décor pour cette case, on l'affiche par dessus l'image de fond
				pixbux_decor = None
				if col['decor'] != None :
					pixbuf_decor = gtk.gdk.pixbuf_new_from_file("/home/loic/Programmation/Calculateur Trajet/media" + col['decor'])
					pixbuf_decor.composite(pixbuf, 0, 0, pixbuf_decor.props.width, pixbuf_decor.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_BILINEAR, 255)

				# Si la case est un changement de zone, on modifie son apparence
				if col['is_passage'] :
					pixbuf_passage = gtk.gdk.pixbuf_new_from_file("/home/loic/Programmation/Calculateur Trajet/media/images/passage.gif")
					pixbuf_passage.composite(pixbuf, 0, 0, pixbuf_passage.props.width, pixbuf_passage.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_BILINEAR, 255)

				coord = str(col['x_coord']) + "," + str(col['y_coord'])
				tooltip = coord + " (" + str(col['time']) + " mins)"
				self.grid.listStore.append([col['time'],pixbuf,tooltip])
				gtk.gdk.threads_leave()

		show_map_time = time.time() - start_time
		print "Durée d'affichage de la carte : %f" % show_map_time

class GridInterface :

	scroll_bar, iconview, listStore = None, None, None

	def __init__(self, data) :
		scroll_bar = gtk.ScrolledWindow()
		scroll_bar.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.gridBox = scroll_bar

		self.listStore = gtk.ListStore(str, gtk.gdk.Pixbuf, str)
		iconview = gtk.IconView()
		iconview.set_model(self.listStore)
		iconview.set_tooltip_column(2)
		iconview.set_pixbuf_column(1)
		iconview.set_columns(121)
		iconview.set_margin(0)
		iconview.set_spacing(0)
		iconview.set_row_spacing(0)
		iconview.set_column_spacing(0)
		iconview.set_item_padding(1)
		self.iconview = iconview
		iconview.props.has_tooltip = True

#		iconview.connect("cursor-changed", self.onCursorChanged, data)
#		iconview.connect("row-activated", self.onActiveRow, data)
#		iconview.connect("query-tooltip", self.on_query_tooltip)
    
		scroll_bar.add(iconview)

class MenuInterface :
  
	menu_bar = None

	def __init__(self, data) :
		# Barre de menu
		self.menu_bar = gtk.MenuBar()

		# Menu Fichier
		menu = gtk.Menu()
		accel = gtk.AccelGroup()
		menu_item = gtk.MenuItem(label="_Fichier")
		menu_item.set_submenu(menu)
		self.menu_bar.append(menu_item)

		# Les éléments du menu Fichier
		menu_item = gtk.ImageMenuItem(gtk.STOCK_QUIT, accel)
		menu_item.set_tooltip_text('Quitter')
		menu_item.connect("activate", data.quit)
		menu.append(menu_item)

		# Menu ?
		menu = gtk.Menu()
		menu_item = gtk.MenuItem(label="?")
		menu_item.set_submenu(menu)
		self.menu_bar.append(menu_item)

		# Les éléments du menu ?
		menu_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
		menu_item.set_tooltip_text('À propos')
		menu_item.connect("activate", About, data)
		menu.append(menu_item)

		data.window.add_accel_group(accel)

class About :
	"Fenêtre about"

	about = None

	def __init__(self, widget, wto) :
		about = gtk.AboutDialog()
#		if os.access(WTO_ICON,os.F_OK) :
#			about.set_icon(gtk.gdk.pixbuf_new_from_file(WTO_ICON))
#			about.set_logo(gtk.gdk.pixbuf_new_from_file(WTO_ICON))
#		about.set_authors(WTO_AUTHORS)
#		about.set_artists(WTO_ARTISTS)
#		about.set_license(WTO_LICENSE)
#		about.set_name('Wto')
#		about.set_version(WTO_VERSION)
#		about.set_comments('Wto est un logiciel libre permettant de regarder la\n Web Tv d\'Orange avec Mplayer sans navigateur\n (tel que Firefox)')
#		about.set_copyright('Copyright (c) 2009 - Papaneo, TuxGasy (alias UgM)\nCopyright (c) 2010 - Loïc GRENON')
#		about.set_website('http://wto.tuxfamily.org')

		about.run()
		about.destroy()

class StatusBarInterface :
  
	status_bar, context_id = None, None

	def addText(self, msg) :
		self.status_bar.push(self.context_id, msg)

	def __init__(self, data) :
		self.status_bar = gtk.Statusbar()
		self.status_bar.show_all()
		self.context_id = self.status_bar.get_context_id("ShowChannel")

def main() :
	t = MainInterface()

if __name__ == '__main__' :
	main()
