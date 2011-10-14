#!/usr/bin/python
# -*- coding: utf-8 -*-

# Gtk
import gtk

import thread

import get_maps

import time

import os
# parseur de config valeur-cle
import ConfigParser

LM_DIRNAME = 'LibertyMap'

# Emplacements dépendants de l'OS
if 'APPDATA' in os.environ:
	LM_CONFIG_PATH = os.path.join(os.environ['APPDATA'], LM_DIRNAME)
elif 'XDG_CONFIG_HOME' in os.environ:
	LM_CONFIG_PATH = os.path.join(os.environ['XDG_CONFIG_HOME'], LM_DIRNAME)
else:
	LM_CONFIG_PATH = os.path.join(os.environ['HOME'], '.config', LM_DIRNAME)

if 'APPDATA' in os.environ:
	LM_CACHE_PATH = os.path.join(LM_CONFIG_PATH, 'cache')
elif 'XDG_CACHE_HOME' in os.environ:
	LM_CACHE_PATH = os.path.join(os.environ['XDG_CACHE_HOME'], LM_DIRNAME)
else:
	LM_CACHE_PATH = os.path.join(os.environ['HOME'], '.cache', LM_DIRNAME)

# Autres emplacements
LM_CONF = os.path.join(LM_CONFIG_PATH, 'LibertyMap.conf')

class MainInterface :
	window, menu, statusBar = None, None, None

	def __init__(self, config) :
		self.config = config
		print 'Initialisation de la fenêtre principale...'
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.connect("destroy", self.quit)
		self.window.set_title('Calculateur de trajet')
		self.window.set_default_size(800, 800)

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

	def onSelectionChange(self, widget) :
		# Griser la case sélectionnée et dégriser celle qui est déselectionnée
		# Utiliser la fonction Gtk::TreeSelection::set_select_function()
		# Ou modifier la propriété selection-box-alpha, si possible
		selected_items = widget.get_selected_items()
		path_time = 0
		for item in selected_items :
			time = self.grid.listStore.get_value(self.grid.listStore.get_iter(item[0]),0)
			time = self.compute_effective_time(int(time))
			path_time += time
		self.statusBar.addText("Temps du trajet : "+str(path_time)+"mins")

	def compute_effective_time(self, time) :
		try :
			reduc_deplacement = self.config.config.getint('talents', 'reduc_deplacement')
		except :
			reduc_deplacement = None

		try :
			talent_rodeur = self.config.config.getboolean('talents', 'rodeur')
		except :
			talent_rodeur = False

		try :
			talent_grimpeur = self.config.config.getboolean('talents', 'grimpeur')
		except :
			talent_grimpeur = False

		try :
			talent_aventurier = self.config.config.getboolean('talents', 'aventurier')
		except :
			talent_aventurier = False

		try :
			talent_randonneur = self.config.config.getboolean('talents', 'randonneur')
		except :
			talent_randonneur = False

		if time == 60 and talent_grimpeur :
			time = 50
		elif time == 50 and talent_aventurier :
			time = 40
		elif time == 40 and talent_randonneur :
			time = 30

		if talent_rodeur :
			time -= time / 10

		time -= reduc_deplacement

		return time

	def CreateWayPixbuf(self) :
		xpmdata = [
			"32 32 2 1",
			"       c None",
			".      c #FF0000",
			"................................",
			"................................",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"..                            ..",
			"................................",
			"................................"
			]

		return gtk.gdk.pixbuf_new_from_xpm_data(xpmdata)

	def ShowMap(self) :
		start_time = time.time()
		try :
			login = self.config.config.get('borgne', 'login')
		except :
			login = None
		try :
			password = self.config.config.get('borgne', 'password')
		except :
			password = None
		map_info = get_maps.get_maps(login, password)
		get_map_time = time.time() - start_time
		print "Durée de récupération des cartes : %f" % get_map_time

		start_time = time.time()
		pixbuf_passage = self.CreateWayPixbuf()
		i = 0
		for row in map_info :
			j = 0
			for col in row :
				gtk.gdk.threads_enter()
				if col['img'] != None :
					pixbuf = gtk.gdk.pixbuf_new_from_file(LM_CACHE_PATH + "/media" + col['img'])
				else :
					pixbuf = gtk.gdk.pixbuf_new_from_file(LM_CACHE_PATH + "/media/images/carregris.gif")

				# S'il y a un décor pour cette case, on l'affiche par dessus l'image de fond
				pixbux_decor = None
				if col['decor'] != None :
					pixbuf_decor = gtk.gdk.pixbuf_new_from_file(LM_CACHE_PATH + "/media" + col['decor'])
					pixbuf_decor.composite(pixbuf, 0, 0, pixbuf_decor.props.width, pixbuf_decor.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_BILINEAR, 255)

				# Si la case est un changement de zone, on modifie son apparence
				if col['is_passage'] :
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
		iconview.set_columns(121)
		iconview.set_margin(0)
		iconview.set_spacing(0)
		iconview.set_row_spacing(0)
		iconview.set_column_spacing(0)
		iconview.set_item_padding(0)
		iconview.set_selection_mode(gtk.SELECTION_MULTIPLE)
		self.iconview = iconview
		iconview.props.has_tooltip = True

		renderer = gtk.CellRendererPixbuf()
		renderer.set_property('follow-state', True)
		iconview.pack_start(renderer)
		iconview.set_attributes(renderer,pixbuf=1)
    
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

class Config :
  
	config = None

	def __init__(self) :
		self.config = ConfigParser.ConfigParser()
		if not os.access(LM_CONF, os.F_OK | os.W_OK) :
			self.config.add_section('borgne')
			self.config.set('borgne', 'login', '')
			self.config.set('borgne', 'password', '')
			
			self.config.add_section('talents')
			self.config.set('talents', 'rodeur', 'false')
			self.config.set('talents', 'grimpeur', 'false')
			self.config.set('talents', 'aventurier', 'false')
			self.config.set('talents', 'randonneur', 'false')
			self.config.set('talents', 'reduc_deplacement', '0')
			
			if not os.access(LM_CONFIG_PATH, os.F_OK) :
				os.makedirs(LM_CONFIG_PATH)
			self.write()
		else :
			self.config.read(LM_CONF)
  
	def write(self) :
		self.config.write(open(LM_CONF, 'wb'))

def main() :
	config = Config()
	t = MainInterface(config)

if __name__ == '__main__' :
	main()
