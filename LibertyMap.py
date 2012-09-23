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
import urllib2
import re
import logging
from common import *

class MainInterface :
	window, menu, statusBar = None, None, None

	def __init__(self, config) :
		self.config = config

		LoggingInterface(LM_LOG)
		self.logger = logging.getLogger('')

		self.graph = []
		self.start_x = 0
		self.start_y = 0
		self.end_x = 0
		self.end_y = 0
		self.extra_time_start = 0
		self.extra_time_end = 0

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
		self.grid.iconview.connect("selection-changed", self.onSelectionChange)
		self.grid.iconview.connect("button-press-event", self.onButtonPressEvent)
		vbox.pack_start(self.grid.gridBox, True, True)

		# Barre d'état
		status_bar = gtk.Toolbar()
		status_bar.set_style(gtk.TOOLBAR_BOTH)
		self.path_time = gtk.ToolButton()
		self.path_time.connect("clicked", self.copy2clipboard)
		status_bar.insert(self.path_time, 0)
		sep = gtk.SeparatorToolItem()
		status_bar.insert(sep, 1)
		self.path_detail = gtk.ToolButton()
		self.path_detail.connect("clicked", self.copy2clipboard)
		status_bar.insert(self.path_detail, 2)
		vbox.pack_start(status_bar, False, False, 0)

		self.window.show_all()

		self.progress_interface = ProgressInterface(self.window)

		thread.start_new_thread(self.getMap, ())

		gtk.gdk.threads_init()
		gtk.gdk.threads_enter()
		gtk.main()
		gtk.gdk.threads_leave()

	def quit(self, widget, data=None) :
		gtk.main_quit()

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

				# Menu clic droit
				tooltip = self.grid.listStore.get_value(self.grid.listStore.get_iter(path), 2)
				pattern = r"[0-9]*,[0-9]* \([0-9]* mins\) - vers Tour.*"

				popup_menu = PopupMenu(self, True) if re.match(pattern, tooltip) else PopupMenu(self)
				popup_menu = popup_menu.popup_menu
				popup_menu.attach_to_widget(self.grid.iconview, None)
				popup_menu.popup(None, None, None, event.button, event.time)
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
		hours, minutes = divmod(path_time, 60)
		self.path_time.set_label("Temps du trajet sélectionné : %ih%imin" % (hours, minutes))
		self.path_detail.set_label('')
		
	def copy2clipboard(self, widget):
		clipboard = widget.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD)
		clipboard.set_text(widget.get_label())
		
	def CalcPath_cb(self, widget) :
		widget.set_sensitive(False)
		self.grid.iconview.unselect_all()
		thread.start_new_thread(self.findPath, (widget,))
		
	def findPath(self, widget):
		gtk.gdk.threads_enter()
		spinner = gtk.Spinner()
		self.path_time.set_icon_widget(spinner)
		self.path_time.set_label('Recherche du trajet en cours ...')
		spinner.show()
		spinner.start()
		gtk.gdk.threads_leave()
		
		graph = copy.deepcopy(self.graph)	# On fait une copie du graphe pour ne pas modifier l'original
		graph[self.start_y][self.start_x].is_start = True
		graph[self.end_y][self.end_x].is_end = True
		algo = astar.PathFinder(graph, self.start_x, self.start_y, self.end_x, self.end_y, time_func = self.compute_effective_time)
		start_time = time.time()
		path = algo.findPath()
		get_path_time = time.time() - start_time
		
		gtk.gdk.threads_enter()
		self.logger.debug("Durée de recherche : %f" % get_path_time)
		gtk.gdk.threads_leave()
		
		if len(path) == 0 :
			message_type = gtk.MESSAGE_ERROR
			title = "Trajet impossible"
			message = "Il n'y a pas de chemin possible de (%i,%i) vers (%i,%i)." % (self.start_x, self.start_y, self.end_x, self.end_y)
			gobject.idle_add(self.show_dialog, message_type, title, message)
		else :
			path_time = algo.path_time + self.extra_time_start + self.extra_time_end
			hours, minutes = divmod(path_time, 60)
			gtk.gdk.threads_enter()
			self.logger.info("Chemin trouvé ! Temps total du trajet : %ih%imin", hours, minutes)
			gtk.gdk.threads_leave()
			
			cases = {}
			for node in path :
				if node.time in cases :
					cases[node.time] += 1
				else :
					cases[node.time] = 1
					
				gtk.gdk.threads_enter()
				self.logger.info("(%i,%i) : %i min" % (node.x,node.y,node.time))
				self.grid.iconview.select_path(node.x + 190 * node.y)
				gtk.gdk.threads_leave()
			
			detail = ''
			for tile_time in sorted(cases.iterkeys()):
				if tile_time != 0 :
					detail += str(cases[tile_time]) + '*' + str(tile_time) + ' + '
			
			gtk.gdk.threads_enter()
			self.path_time.set_label("Temps du trajet : %ih%imin" % (hours, minutes))
			self.path_detail.set_label(detail[:-3])
			gtk.gdk.threads_leave()
			
		gtk.gdk.threads_enter()
		spinner.stop()
		self.path_time.set_icon_widget(None)
		widget.set_sensitive(True)
		gtk.gdk.threads_leave()
		
	def show_dialog(self, message_type, title, message):
		gtk.gdk.threads_enter()
		dialog = gtk.MessageDialog(parent=self.window, type=message_type, buttons=gtk.BUTTONS_OK, message_format=title)
		dialog.format_secondary_text(message)
		dialog.run()
		dialog.destroy()
		gtk.gdk.threads_leave()

	def ClearPath_cb(self, widget) :
		self.grid.iconview.unselect_all()

	def Prefs_cb(self, widget) :
		PrefsInterface(self.window, self.config)
		
	def Scrot_cb(self, widget) :
		file_chooser = gtk.FileChooserDialog("Capture du trajet", self.window, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		file_chooser.set_do_overwrite_confirmation(True)
		file_chooser.set_current_name("Trajet.png")

		file_filter = gtk.FileFilter()
		file_filter.set_name("PNG")
		file_filter.add_mime_type("image/png")
		file_filter.add_pattern("*.png")
		file_chooser.add_filter(file_filter)
		
		file_filter = gtk.FileFilter()
		file_filter.set_name("All files")
		file_filter.add_pattern("*")
		file_chooser.add_filter(file_filter)
		
		response = file_chooser.run()
		result = ""
		if response == gtk.RESPONSE_OK:
			result = file_chooser.get_filename()
		file_chooser.destroy()
		
		if result != "" :
			filename, extension = os.path.splitext(result)
			if not filename.endswith('.png') :
				filename += '.png'
		
			width, height = self.window.get_size()
			pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
			screenshot = pixbuf.get_from_drawable(self.window.window, self.window.get_colormap(), 0, 0, 0, 0, width, height)
			screenshot.save(filename, 'png')

	def compute_effective_time(self, time) :
		if time == 0 :	# Si la case a un coût nul, il n'y a pas de réduction possible
			return 0

		try :
			reduc_deplacement = self.config.config.getint('talents', 'reduc_deplacement')
		except :
			reduc_deplacement = 0

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
		
		if time < 1 :	# Le temps d'une case ne peut pas être négatif ou nul
			time = 1

		return time

	def CreateXPM(self, bg_color=None, width=32, height=32, border_width=0, border_color=None) :
		xpm_data = ["%i %i 2 1" % (width, height)]
		xpm_data.append("  c %s" % bg_color)
		xpm_data.append(". c %s" % border_color)

		# Bordure supérieure
		for y in xrange(border_width) :
			xpm_data.append("".join("." for x in range(width)))
		# Corps et bordures latérales
		for y in xrange(height-2*border_width) :
			xpm_data.append("".join("." for x in range(border_width)) + "".join(" " for x in range(width-2*border_width)) + "".join("." for x in range(border_width)))
		# Bordure inférieure
		for y in xrange(border_width) :
			xpm_data.append("".join("." for x in range(width)))

		return gtk.gdk.pixbuf_new_from_xpm_data(xpm_data)

	def getMap(self) :
		try :
			local_md5_mapfile = self.config.config.get('general', 'md5_mapfile')
		except :
			local_md5_mapfile = ''

		try :
			url_req = urllib2.urlopen('http://libertymap.difoolou.net/map.md5sum')
			distant_md5_mapfile = url_req.read(32)
		except : # Si on n'arrive pas à récupérer le MD5SUM du fichier distant, on considère que le fichier local est à jour
			distant_md5_mapfile = local_md5_mapfile

		# Si la carte n'est pas à jour ou que l'on arrive pas à la lire, on la télécharge
		if local_md5_mapfile != distant_md5_mapfile or not os.access(LM_MAP, os.F_OK):
			self.logger.debug("Carte obsolète : Téléchargement de la nouvelle carte en cours ...")
			url_req = urllib2.urlopen('http://libertymap.difoolou.net/map.xml.gz')
			CHUNK = 16 * 1024
			ensure_dir(LM_MAP)
			with open(LM_MAP, 'wb') as fp:
				for chunk in iter(lambda: url_req.read(CHUNK), ''):
					fp.write(chunk)

			self.config.config.set('general', 'md5_mapfile', distant_md5_mapfile)
			self.config.write()
			self.config.config.read(LM_CONF)

		self.graph, img_list = get_maps.get_map(LM_MAP)
		new_img_list = get_maps.check_images(img_list)
		getImage = self.getImages(new_img_list)
		gobject.idle_add(getImage.next)

	def getImages(self, img_list) :
		# http://faq.pygtk.org/index.py?req=show&file=faq23.020.htp
		# http://stackoverflow.com/questions/8778587/is-there-a-way-to-continue-only-when-gobject-idle-add-function-terminate/8779184
		start_time = time.time()
		nb_img = len(img_list)
		i = 1.0
		for img in img_list :
			self.progress_interface.set_progress(i, nb_img)
			gtk.gdk.threads_enter()
			if not get_maps.download_image(img) :
				self.logger.error("Echec de téléchargement de l'image %s" % img)
			gtk.gdk.threads_leave()
			i += 1.0
			yield True
		self.progress_interface.progressbar_img.set_text("Les images sont à jour")
		self.progress_interface.progressbar_img.set_fraction(1)
		get_map_time = time.time() - start_time
		self.logger.debug("Durée de récupération des images : %f" % get_map_time)
		map_loader = self.loadMap()
		gobject.idle_add(map_loader.next)
		yield False

	def loadMap(self, step=128) :
		# http://faq.pygtk.org/index.py?req=show&file=faq13.043.htp
		# http://stackoverflow.com/questions/8778587/is-there-a-way-to-continue-only-when-gobject-idle-add-function-terminate/8779184
		start_time = time.time()
		i = 1.0
		nb_tiles = len(self.graph) * len(self.graph[0])
		pixbuf_passage = self.CreateXPM(border_width=2, border_color="#FF0000")
		missing_pixbuf = self.CreateXPM(bg_color="#808080")
		self.grid.iconview.freeze_child_notify()
		for row in self.graph :
			for col in row :	# col is an astar.Node instance
				if col.img_base != None :
					image_path = os.path.join(LM_CACHE_PATH,"media" + os.sep + col.img_base)
					pixbuf = gtk.gdk.pixbuf_new_from_file(image_path).scale_simple(32, 32, gtk.gdk.INTERP_NEAREST) if os.access(image_path, os.F_OK) else missing_pixbuf
				else :
					pixbuf = missing_pixbuf

				# S'il y a un décor pour cette case, on l'affiche par dessus l'image de fond
				if col.img_decor != None :
					image_path = os.path.join(LM_CACHE_PATH,"media" + os.sep + col.img_decor)
					if os.access(image_path, os.F_OK) :
						pixbuf_decor = gtk.gdk.pixbuf_new_from_file(image_path)
						pixbuf_decor.composite(pixbuf, 0, 0, pixbuf_decor.props.width, pixbuf_decor.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_NEAREST, 255)

				# S'il y a un PNJ pour cette case, on l'affiche par dessus le décor
				if col.img_pnj != None :
					image_path = os.path.join(LM_CACHE_PATH,"media" + os.sep + col.img_pnj)
					if os.access(image_path, os.F_OK) :
						pixbuf_pnj = gtk.gdk.pixbuf_new_from_file(image_path)
						pixbuf_pnj.composite(pixbuf, 0, 0, pixbuf_pnj.props.width, pixbuf_pnj.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_NEAREST, 255)

				# Si la case est un changement de zone, on modifie son apparence
				if col.passage :
					pixbuf_passage.composite(pixbuf, 0, 0, pixbuf_passage.props.width, pixbuf_passage.props.height, 0, 0, 1.0, 1.0, gtk.gdk.INTERP_NEAREST, 255)

				coord = str(col.x) + "," + str(col.y)
				
				if col.passage_name :
					tooltip = coord + " - " + str(col.passage_name)
				elif col.pnj_name :
					tooltip = coord + " - " + str(col.pnj_name)
				else :
					tooltip = coord + " (" + str(col.time) + " mins)"
				self.grid.listStore.append([col.time, pixbuf, tooltip, col.x, col.y])

				self.progress_interface.progressbar_map.set_fraction(i/nb_tiles)
				self.progress_interface.progressbar_map.set_text("Chargement des tuiles en cours ...")
				i += 1.0
				if (i % step) == 0:
					self.grid.iconview.thaw_child_notify()
					yield True
					self.grid.iconview.freeze_child_notify()
		self.grid.iconview.set_model(self.grid.listStore)
		self.grid.iconview.thaw_child_notify()
		show_map_time = time.time() - start_time
		self.logger.debug("Durée d'affichage de la carte : %f" % show_map_time)
		# On retire la fenetre d'affichage de l'avancement des différents téléchargements, chargements, etc ...
		self.progress_interface.window.destroy()
		yield False

	def onChangeStartPos(self, widget, extra_tiles=None) :
		iconview = widget.get_parent().get_attach_widget()
		liststore = iconview.get_model()
		path = iconview.get_cursor()[0]
		x_coord = liststore.get_value(liststore.get_iter(path), 3)
		y_coord = liststore.get_value(liststore.get_iter(path), 4)
		self.logger.info("Changement des coordonnées de départ : (%i, %i)" % (x_coord, y_coord))
		self.start_x = x_coord
		self.start_y = y_coord
		#self.startPos = astar.Node(x_coord, y_coord, None, time)
		self.extra_time_start = 0
		if extra_tiles :
			for tile_time, tile_nb in extra_tiles.items() :
				self.extra_time_start += tile_nb * self.compute_effective_time(tile_time)

	def onChangeEndPos(self, widget, extra_tiles=None) :
		iconview = widget.get_parent().get_attach_widget()
		liststore = iconview.get_model()
		path = iconview.get_cursor()[0]
		x_coord = liststore.get_value(liststore.get_iter(path), 3)
		y_coord = liststore.get_value(liststore.get_iter(path), 4)
		self.logger.info("Changement des coordonnées d'arrivée : (%i, %i)" % (x_coord, y_coord))
		self.end_x = x_coord
		self.end_y = y_coord
		#self.endPos = astar.Node(x_coord, y_coord, None, time)
		self.extra_time_end = 0
		if extra_tiles :
			for tile_time, tile_nb in extra_tiles.items() :
				self.extra_time_end += tile_nb * self.compute_effective_time(tile_time)

class LoggingInterface :

	def __init__(self, filename) :
		logging.basicConfig(
			filename=filename,
			filemode='w',
			level=logging.DEBUG,
			format='%(asctime)s %(levelname)s - %(message)s',
			datefmt='%d/%m/%Y %H:%M:%S',
			)
#		console = logging.StreamHandler()
		# set a format which is simpler for console use
#		formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
		# tell the handler to use this format
#		console.setFormatter(formatter)
		# add the handler to the root logger
#		logging.getLogger('').addHandler(console)

class GridInterface :

	scroll_bar, iconview, listStore = None, None, None

	def __init__(self, data) :
		scroll_bar = gtk.ScrolledWindow()
		scroll_bar.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.gridBox = scroll_bar
		# ListStore columns : time, pixbuf, tooltip, x_coord, y_coord, passage
		self.listStore = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT)
		iconview = gtk.IconView()
		iconview.set_tooltip_column(2)
		iconview.set_columns(190)
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

class ProgressInterface :

	def __init__(self, parent_window) :
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_default_size(400, 100)
		self.window.set_deletable(False)
		self.window.set_transient_for(parent_window)
		self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

		vbox = gtk.VBox(False, True)
		self.window.add(vbox)

		self.label = gtk.Label("Téléchargement de l'image")
		vbox.pack_start(self.label, False)

		self.progressbar_img = gtk.ProgressBar()
		vbox.pack_start(self.progressbar_img, False)

		self.progressbar_map = gtk.ProgressBar()
		vbox.pack_start(self.progressbar_map, False)

		self.window.show_all()

	def set_progress(self, current, total) :
		self.progressbar_img.set_text("Téléchargement de l'image %i/%i" % (current, total))
		self.progressbar_img.set_fraction(current/total)

class PopupMenu :

	def __init__(self, data, tour=False) :
		self.popup_menu = gtk.Menu()
		if tour :
			popup_item = gtk.MenuItem("Départ depuis le bas de la tour")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeStartPos)
			popup_item.show()

			popup_item = gtk.MenuItem("Départ depuis l'hosto")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeStartPos, {15:18, 1:6})
			popup_item.show()

			popup_item = gtk.MenuItem("Arrivée en bas de la tour")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeEndPos)
			popup_item.show()

			popup_item = gtk.MenuItem("Arrivée sur un point du bas")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeEndPos, {15:9})
			popup_item.show()

			popup_item = gtk.MenuItem("Arrivée sur le point milieu")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeEndPos, {15:11})
			popup_item.show()

			popup_item = gtk.MenuItem("Arrivée sur un point du haut")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeEndPos, {15:14})
			popup_item.show()

			popup_item = gtk.MenuItem("Arrivée sur le point extérieur")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeEndPos, {15:18})
			popup_item.show()

		else :
			popup_item = gtk.MenuItem("Départ")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeStartPos)
			popup_item.show()

			popup_item = gtk.MenuItem("Arrivée")
			self.popup_menu.append(popup_item)
			popup_item.connect("activate", data.onChangeEndPos)
			popup_item.show()

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
		menu_item.connect("activate", About)
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
		
		scrot_b = gtk.ToolButton(gtk.STOCK_SAVE_AS)
		scrot_b.set_label("Capture")
		scrot_b.set_tooltip_text("Prendre une capture d'écran")
		scrot_b.connect("clicked", data.Scrot_cb)
		self.tool_bar.insert(scrot_b, 2)

		prefs_b = gtk.ToolButton(gtk.STOCK_PREFERENCES)
		prefs_b.set_label("Préférences")
		prefs_b.set_tooltip_text("Modifier les préférences")
		prefs_b.connect("clicked", data.Prefs_cb)
		self.tool_bar.insert(prefs_b, 3)
		
class About :
	"Fenêtre about"

	def __init__(self, widget) :
		about = gtk.AboutDialog()
		if os.access(APP_ICON,os.F_OK) :
			about.set_icon(gtk.gdk.pixbuf_new_from_file(APP_ICON))
			about.set_logo(gtk.gdk.pixbuf_new_from_file(APP_ICON))
		about.set_authors([author + '\n' for author in APP_AUTHORS])
		about.set_license(APP_LICENSE)
		about.set_name(APP_NAME)
		about.set_version(APP_VERSION)
		about.set_comments(APP_DESCRIPTION)
		about.set_copyright(APP_COPYRIGHT)
		about.set_website(APP_WEBSITE)

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
			self.config.add_section('general')
			self.config.set('general', 'md5_mapfile', '')
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

		try :
			conf_value = config.config.getboolean('talents', 'rodeur')
		except :
			conf_value = False
		self.talt_rodeur_btn = TalentCheckButton("Rodeur", initial_state = conf_value)
		self.talt_rodeur_btn.set_tooltip_markup('Gain de 10% sur chaque case traversée.')
		vbox.pack_start(self.talt_rodeur_btn , False)

		try :
			conf_value = config.config.getboolean('talents', 'grimpeur')
		except :
			conf_value = False
		self.talt_grimpeur_btn = TalentCheckButton("Grimpeur", initial_state = conf_value, parent_button = self.talt_rodeur_btn)
		self.talt_grimpeur_btn.set_tooltip_markup('Gain de 10min sur les cases de montagne à 60min de base.')
		vbox.pack_start(self.talt_grimpeur_btn , False)

		try :
			conf_value = config.config.getboolean('talents', 'aventurier')
		except :
			conf_value = False
		self.talt_aventurier_btn = TalentCheckButton("Aventurier", initial_state = conf_value, parent_button = self.talt_grimpeur_btn)
		self.talt_aventurier_btn.set_tooltip_markup('Gain de 10min sur les cases de jungle dense à 50min de base.')
		vbox.pack_start(self.talt_aventurier_btn , False)

		try :
			conf_value = config.config.getboolean('talents', 'randonneur')
		except :
			conf_value = False
		self.talt_randonneur_btn = TalentCheckButton("Randonneur", initial_state = conf_value, parent_button = self.talt_aventurier_btn)
		self.talt_randonneur_btn.set_tooltip_markup('Gain de 10min sur les cases de forêt à 40min de base.')
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
		if not config.config.has_section("general") :
			config.config.add_section("general")
			
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

class TalentCheckButton(gtk.CheckButton) :
	def __init__(self, label=None, use_underline=True, initial_state = False, parent_button = None) :
		gtk.CheckButton.__init__(self, label, use_underline)
		self.set_active(initial_state)
		self.connect("clicked", self.__on_toggled)
		self.child_button = None
		self.set_parent_button(parent_button)

	def set_parent_button(self, parent_button) :
		self.parent_button = parent_button
		if parent_button :
			parent_button.child_button = self

		self.__on_toggled(self)

	def __on_toggled(self, button) :
		if self.parent_button :
			if self.parent_button.get_active() :
				self.set_sensitive(True)
				if self.child_button :
					if self.get_active() :
						self.parent_button.set_sensitive(False)
						self.child_button.set_sensitive(True)
					else :
						self.child_button.set_sensitive(False)
						self.parent_button.set_sensitive(True)
				else :
					self.parent_button.set_sensitive(not self.get_active())
			else :
				self.set_sensitive(False)
				if self.child_button :
					self.child_button.set_sensitive(False)
		else :
			if self.child_button :
				self.child_button.set_sensitive(self.get_active())

def main() :
	config = Config()
	MainInterface(config)

if __name__ == '__main__' :
	main()
