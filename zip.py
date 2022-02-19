"""Adds Extra Here and Extra To... to the context menu."""

import threading
import time
import os

from gi.repository import Caja, GLib, GObject, Gtk
from zipfile import ZipFile


class ProgressBar():
    """Window for the progress bar."""
    def __init__(self, path, files):
        """Initializes the progress bar."""
        self._window = Gtk.Window(default_height=50, default_width=300)
        self._window.connect('destroy', Gtk.main_quit)

        self._path = path
        self._files = files

        self._progress = Gtk.ProgressBar(show_text=True)
        self._window.add(self._progress)
        self._thread = threading.Thread(target=self._target)

    def _update_progress(self, i):
        """Updates the progress bar."""
        self._progress.pulse()
        self._progress.set_text(str(i))

        return False

    def _target(self):
        """Target for progress bar."""
        total = len(self._files)
        for i, file in enumerate(self._files):
            name = file.get_name()
            file_name = os.path.join(self._path, name)
            percentage = int(i / total * 100)
            progress = f'Extracting {name}   {percentage}%   ({i}/{total})'

            if file_name.endswith('.zip'):
                GLib.idle_add(self._update_progress, progress)
                with ZipFile(file_name, 'r') as zip:
                    zip.extractall()

            time.sleep(0.2)

        Gtk.Window.destroy(self._window)

    def start(self):
        """Start the progress bar."""
        self._window.show_all()
        self._thread.daemon = True
        self._thread.start()


class UnzipMenuProvider(GObject.GObject, Caja.MenuProvider):
    def _extract_here(self, menu, files: 'list[CajaVFSFile]'):
        """Extracts selected files to current location."""
        # Change to correct directory
        path = os.path.dirname(files[0].get_location().get_path())
        os.chdir(path)
        progress = ProgressBar(path, files)
        progress.start()
        Gtk.main()

    def get_file_items(self, window, files: 'list[CajaVFSFile]'):
        """Gets files selected and connects functions."""
        # Set up the top menu with a submenu
        top_menu_item = Caja.MenuItem(
                name='UnzipMenuProvider::Unzip',
                label='Unzip',
                tip='',
                icon='')

        submenu = Caja.Menu()
        top_menu_item.set_submenu(submenu)

        # Setup the extra here command
        extract_here = Caja.MenuItem(
                name='UnzipMenuProvider::Extract Here',
                label='Extract Here',
                tip='',
                icon='')

        submenu.append_item(extract_here)
        all_files = files.copy()
        extract_here.connect('activate', self._extract_here, all_files)

        extract_to_menu_item = Caja.MenuItem(
                name='UnzipMenuProvider::Extract To',
                label='Extract To',
                tip='',
                icon='')
        submenu.append_item(extract_to_menu_item)

        return top_menu_item,

    def get_background_items(self, window, file):
        """Gets all the background items."""
        submenu = Caja.Menu()
        submenu.append_item(Caja.MenuItem(
            name='UnzipMenuProvider::Bar2',
            label='Bar2',
            tip='',
            icon=''))

        menuitem = Caja.MenuItem(
                name='UnzipMenuProvider::Foo2',
                label='Foo2',
                tip='',
                icon='')
        menuitem.set_submenu(submenu)

        return menuitem,