#!/usr/bin/python
# -*- coding: utf-8 -*-

# Gtk
import gtk, gobject

import thread

import get_maps

import time

import os
# parseur de config valeur-cle
import ConfigParser

import astar

import copy

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
		self.graph = []
		self.start_x = 0
		self.start_y = 0
		self.end_x = 0
		self.end_y = 0
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
		
		# Toolbar
		self.tool_bar = ToolBarInterface(self)
		vbox.pack_start(self.tool_bar.tool_bar, False, True)

		# Grille
		self.grid = GridInterface(self)
		self.grid.iconview.connect("item-activated", self.onActiveItem)
		self.grid.iconview.connect("selection-changed", self.onSelectionChange)
		self.grid.iconview.connect("button-press-event", self.onButtonPressEvent)
		vbox.pack_start(self.grid.gridBox, True, True)

		# Barre d'état
		self.statusBar = StatusBarInterface(self)
		vbox.pack_start(self.statusBar.status_bar, False, False, 0)

		# Menu clic droit
		self.popup_menu = PopupMenu(self)
		self.popup_menu = self.popup_menu.popup_menu
		self.popup_menu.attach_to_widget(self.grid.iconview, None)

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

	def onButtonPressEvent(self, iconview, event):
		if event.button == 3:
			x = int(event.x)
			y = int(event.y)
			pthinfo = iconview.get_item_at_pos(x, y)
			if pthinfo is not None:
				path, renderer = pthinfo
				iconview.grab_focus()
				iconview.set_cursor(path, renderer)
				iconview.select_path(path)
				self.popup_menu.popup(None, None, None, event.button, event.time)
			return True

		if event.button == 1:
			x = int(event.x)
			y = int(event.y)
			pthinfo = iconview.get_item_at_pos(x, y)
			if pthinfo is not None:
				path, renderer = pthinfo
				if iconview.path_is_selected(path) :
					iconview.unselect_path(path)
				else :
					iconview.select_path(path)
			return True

	def onSelectionChange(self, widget) :
		selected_items = widget.get_selected_items()
		path_time = 0
		for item in selected_items :
			time = self.grid.listStore.get_value(self.grid.listStore.get_iter(item[0]),0)
			time = self.compute_effective_time(int(time))
			path_time += time
		self.statusBar.addText("Temps du trajet : "+str(path_time)+"mins")

	def CalcPath_cb(self, widget) :
		graph = copy.deepcopy(self.graph)	# On fait une copie du graphe pour ne pas modifier l'original
		algo = astar.PathFinder(graph, self.start_x, self.start_y, self.end_x, self.end_y)
		start_time = time.time()
		path = algo.findPath()
		get_path_time = time.time() - start_time
		print "Durée de recherche : %f" % get_path_time
		self.grid.iconview.unselect_all()
		for node in path :
			print "(%i,%i)" % (node.x,node.y)
			self.grid.iconview.select_path(node.x + 121 * node.y)

	def ClearPath_cb(self, widget) :
		self.grid.iconview.unselect_all()

	def Prefs_cb(self, widget) :
		pref_window = PrefsInterface(self.window, self.config)

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
		self.graph = get_maps.get_maps(login, password)
		get_map_time = time.time() - start_time
		print "Durée de récupération des cartes : %f" % get_map_time

		start_time = time.time()
		pixbuf_passage = self.CreateWayPixbuf()
		i = 0
		for row in self.graph :
			j = 0
			for col in row :
				# col is an astar.Node instance

				gtk.gdk.threads_enter()
				passage = False

				if col.img_base != None :
					pixbuf = gtk.gdk.pixbuf_new_from_file(LM_CACHE_PATH + "/media" + col.img_base)
				else :
					pixbuf = gtk.gdk.pixbuf_new_from_file(LM_CACHE_PATH + "/media/images/carregris.gif")

				# S'il y a un décor pour cette case, on l'affiche par dessus l'image de fond
				pixbux_decor = None
				if col.img_decor != None :
					pixbuf_decor = gtk.gdk.pixbuf_new_from_file(LM_CACHE_PATH + "/media" + col.img_decor)
					pixbuf_decor.composite(pixbuf, 0, 0, pixbuf_decor.props.width, pixbuf_decor.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_BILINEAR, 255)

				# Si la case est un changement de zone, on modifie son apparence
				if col.passage :
					passage = True
					pixbuf_passage.composite(pixbuf, 0, 0, pixbuf_passage.props.width, pixbuf_passage.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_BILINEAR, 255)

				coord = str(col.x) + "," + str(col.y)
				tooltip = coord + " (" + str(col.time) + " mins)"
				self.grid.listStore.append([col.time, pixbuf, tooltip, col.x, col.y])
				gtk.gdk.threads_leave()

		show_map_time = time.time() - start_time
		print "Durée d'affichage de la carte : %f" % show_map_time

	def onChangeStartPos(self, widget, data=None) :
		iconview = widget.get_parent().get_attach_widget()
		liststore = iconview.get_model()
		path = iconview.get_cursor()[0]
		x_coord = liststore.get_value(liststore.get_iter(path), 3)
		y_coord = liststore.get_value(liststore.get_iter(path), 4)
		print "Changement des coordonnées de départ : (%i, %i)" % (x_coord, y_coord)
		self.start_x = x_coord
		self.start_y = y_coord
		#self.startPos = astar.Node(x_coord, y_coord, None, time)

	def onChangeEndPos(self, widget, data=None) :
		iconview = widget.get_parent().get_attach_widget()
		liststore = iconview.get_model()
		path = iconview.get_cursor()[0]
		x_coord = liststore.get_value(liststore.get_iter(path), 3)
		y_coord = liststore.get_value(liststore.get_iter(path), 4)
		print "Changement des coordonnées d'arrivée : (%i, %i)" % (x_coord, y_coord)
		self.end_x = x_coord
		self.end_y = y_coord
		#self.endPos = astar.Node(x_coord, y_coord, None, time)

class GridInterface :

	scroll_bar, iconview, listStore = None, None, None

	def __init__(self, data) :
		scroll_bar = gtk.ScrolledWindow()
		scroll_bar.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.gridBox = scroll_bar
		# ListStore columns : time, pixbuf, tooltip, x_coord, y_coord, passage
		self.listStore = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT)
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
		iconview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("#000000"))
		self.iconview = iconview
		iconview.props.has_tooltip = True

		renderer = gtk.CellRendererPixbuf()
		renderer.set_property('follow-state', True)
		iconview.pack_start(renderer)
		iconview.set_attributes(renderer,pixbuf=1)
    
		scroll_bar.add(iconview)

class PopupMenu :

	def __init__(self, data) :
		self.popup_menu = gtk.Menu()

		popup_item = gtk.MenuItem("Départ")
		popup_item.show()
		popup_item.connect("activate", data.onChangeStartPos)
		self.popup_menu.append(popup_item)

		popup_item = gtk.MenuItem("Arrivée")
		popup_item.show()
		popup_item.connect("activate", data.onChangeEndPos)
		self.popup_menu.append(popup_item)

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

class ToolBarInterface :

	tool_bar = None

	def __init__(self, data) :
		self.tool_bar = gtk.Toolbar()
		self.tool_bar.set_style(gtk.TOOLBAR_BOTH)

		path_calc_b = gtk.ToolButton(gtk.STOCK_EXECUTE)
		path_calc_b.set_label("Calculer")
		path_calc_b.set_tooltip_text("Calculer le trajet")
		path_calc_b.connect("clicked", data.CalcPath_cb)
		self.tool_bar.insert(path_calc_b, 0)

		clear_path_b = gtk.ToolButton(gtk.STOCK_DELETE)
		clear_path_b.set_label("Effacer")
		clear_path_b.set_tooltip_text("Effacer le trajet courant")
		clear_path_b.connect("clicked", data.ClearPath_cb)
		self.tool_bar.insert(clear_path_b, 1)

		prefs_b = gtk.ToolButton(gtk.STOCK_PREFERENCES)
		prefs_b.set_tooltip_text("Modifier les préférences")
		prefs_b.connect("clicked", data.Prefs_cb)
		self.tool_bar.insert(prefs_b, 2)

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

class PrefsInterface :

	def __init__(self, parent, config) :
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title('Préférences')
		self.window.set_default_size(400, 200)
		self.window.set_transient_for(parent)
		self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

		main_vbox = gtk.VBox(False)
		self.window.add(main_vbox)

		notebook = gtk.Notebook()
		main_vbox.pack_start(notebook)

		vbox = gtk.VBox(False)

		label = gtk.Label("Login")
		label.set_alignment(0,0.5)
		vbox.pack_start(label, False)
		self.login = gtk.Entry()
		try :
			conf_value = config.config.get('borgne', 'login')
		except :
			conf_value = ''
		self.login.set_text(conf_value)
		vbox.pack_start(self.login, False)

		label = gtk.Label("Password")
		label.set_alignment(0,0.5)
		vbox.pack_start(label, False)
		self.password = gtk.Entry()
		self.password.set_visibility(False)
		try :
			conf_value = config.config.get('borgne', 'password')
		except :
			conf_value = ''
		self.password.set_text(conf_value)
		vbox.pack_start(self.password, False)

		label = gtk.Label("Borgne")
		notebook.append_page(vbox, label)

		vbox = gtk.VBox(False)

		self.talt_rodeur_btn = gtk.CheckButton("Rodeur")
		try :
			conf_value = config.config.getboolean('talents', 'rodeur')
		except :
			conf_value = False
		self.talt_rodeur_btn.set_active(conf_value)
		vbox.pack_start(self.talt_rodeur_btn , False)

		self.talt_grimpeur_btn = gtk.CheckButton("Grimpeur")
		try :
			conf_value = config.config.getboolean('talents', 'grimpeur')
		except :
			conf_value = False
		self.talt_grimpeur_btn.set_active(conf_value)
		vbox.pack_start(self.talt_grimpeur_btn , False)

		self.talt_aventurier_btn = gtk.CheckButton("Aventurier")
		try :
			conf_value = config.config.getboolean('talents', 'aventurier')
		except :
			conf_value = False
		self.talt_aventurier_btn.set_active(conf_value)
		vbox.pack_start(self.talt_aventurier_btn , False)

		self.talt_randonneur_btn = gtk.CheckButton("Randonneur")
		try :
			conf_value = config.config.getboolean('talents', 'randonneur')
		except :
			conf_value = False
		self.talt_randonneur_btn.set_active(conf_value)
		vbox.pack_start(self.talt_randonneur_btn , False)

		vbox_reduc = gtk.VBox(False)
		label = gtk.Label("Réduction déplacement")
		label.set_alignment(0,0.5)
		vbox_reduc.pack_start(label, False)
		self.reduc_depl = gtk.SpinButton()
		self.reduc_depl.set_numeric(True)
		self.reduc_depl.set_range(0, 20)
		self.reduc_depl.set_increments(1, 1)
		self.reduc_depl.set_wrap(True)
		self.reduc_depl.set_snap_to_ticks(True)
		try :
			conf_value = config.config.getint('talents', 'reduc_deplacement')
		except :
			conf_value = 0
		self.reduc_depl.set_value(conf_value)
		vbox_reduc.pack_start(self.reduc_depl , False)
		vbox.pack_start(vbox_reduc, False)

		label = gtk.Label("Talents")
		notebook.append_page(vbox, label)

		button_box = gtk.HButtonBox()
		button_box.set_layout(gtk.BUTTONBOX_END)
		button_box.set_spacing(20)
		main_vbox.pack_start(button_box)

		button = gtk.Button(stock=gtk.STOCK_OK)
		button.connect("clicked", self.update, config)
		button_box.add(button)

		button = gtk.Button(stock=gtk.STOCK_CANCEL)
		button.connect("clicked", self.close)
		button_box.add(button)

		self.window.show_all()

	def close(self, button) :
		self.window.destroy()

	def update(self, button, config) :
		if not config.config.has_section("borgne") :
			config.config.add_section("borgne")

		config.config.set("borgne", "login", self.login.get_text())
		config.config.set("borgne", "password", self.password.get_text())

		if not config.config.has_section("talents") :
			config.config.add_section("talents")

		config.config.set("talents", "rodeur", self.talt_rodeur_btn.get_active())
		config.config.set("talents", "grimpeur", self.talt_grimpeur_btn.get_active())
		config.config.set("talents", "aventurier", self.talt_aventurier_btn.get_active())
		config.config.set("talents", "randonneur", self.talt_randonneur_btn.get_active())
		config.config.set("talents", "reduc_deplacement", int(self.reduc_depl.get_value()))
		config.write()

		# On charge la nouvelle configuration
		config.config.read(LM_CONF)

		self.window.destroy()

def main() :
	config = Config()
	t = MainInterface(config)

if __name__ == '__main__' :
	main()
