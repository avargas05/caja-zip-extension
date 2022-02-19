"""Adds Extra Here and Extra To... to the context menu."""

import threading
import time
import os

from gi.repository import Caja, GLib, GObject, Gtk
from zipfile import ZipFile


class ProgressBar():
    """Window for the progress bar."""
    def __init__(self, path, files, target_path=''):
        """Initializes the progress bar."""
        self._window = Gtk.Window(default_height=50, default_width=300)
        self._window.connect('destroy', Gtk.main_quit)

        self._path = path
        self._files = files
        self._target_path = target_path

        self._progress = Gtk.ProgressBar(show_text=True)
        self._window.add(self._progress)
        self._thread = threading.Thread(target=self._target)

    def _update_progress(self, status):
        """Updates the progress bar."""
        self._progress.pulse()
        self._progress.set_text(str(status))

        return False

    def _target(self):
        """Target for progress bar."""
        total = len(self._files)
        for i, file in enumerate(self._files):
            # Form full path name
            name = file.get_name()
            file_name = os.path.join(self._path, name)

            # Status description
            percentage = int(i / total * 100)
            progress = f'Extracting {name}   {percentage}%   ({i}/{total})'

            if file_name.endswith('.zip'):
                GLib.idle_add(self._update_progress, progress)
                with ZipFile(file_name, 'r') as zip:
                    if not self._target_path:
                        zip.extractall()
                    else:
                        zip.extractall(self._target_path)

            time.sleep(0.2)

        Gtk.Window.destroy(self._window)

    def start(self):
        """Start the progress bar."""
        self._window.show_all()
        self._thread.daemon = True
        self._thread.start()


def select_folder():
    """Dialog box for choosing a directory to extract to."""
    action = Gtk.FileChooserAction.SELECT_FOLDER
    dialog = Gtk.FileChooserDialog(
            'Select..',
            None,
            action,
            ('Cancel', Gtk.ResponseType.CANCEL, 'Ok', Gtk.ResponseType.ACCEPT)
        )

    dialog.connect('destroy', Gtk.main_quit)
    response = dialog.run()
    directory = ''
    if response == Gtk.ResponseType.ACCEPT:
        directory = dialog.get_filename()

    dialog.destroy()
    return directory


class UnzipMenuProvider(GObject.GObject, Caja.MenuProvider):
    """Context menu for commands."""
    def _extract_here(self, menu, files):
        """Extracts selected files to current location."""
        # Change to current directory to extract to
        path = os.path.dirname(files[0].get_location().get_path())
        os.chdir(path)

        # Commence extraction and progress bar
        progress = ProgressBar(path, files)
        progress.start()
        Gtk.main()

    def _extract_to(self, menu, files):
        """Extracts selected files to chosen location."""
        # Open dialog box for choosing a folder
        directory = select_folder()
        if directory:
            # Get current directory forming full path name
            path = os.path.dirname(files[0].get_location().get_path())
            os.chdir(path)

            # Commence extraction and progress
            progress = ProgressBar(path, files, directory)
            progress.start()
            Gtk.main()

    def get_file_items(self, window, files):
        """Gets files selected and connects functions."""
        # Important to get copy since selecting a file during extraction
        # changes list of files and locks up the instance of Caja
        all_files = files.copy()

        # Set up the top menu with a submenu
        top_menu_item = Caja.MenuItem(
                name='UnzipMenuProvider::Unzip',
                label='Zip Menu',
                tip='',
                icon='')

        submenu = Caja.Menu()
        top_menu_item.set_submenu(submenu)

        # Setup the extract here command
        extract_here_menu_item = Caja.MenuItem(
                name='UnzipMenuProvider::Extract Here',
                label='Extract Here',
                tip='',
                icon='')

        submenu.append_item(extract_here_menu_item)
        extract_here_menu_item.connect(
                'activate',
                self._extract_here,
                all_files)

        # Setup the extract to command
        extract_to_menu_item = Caja.MenuItem(
                name='UnzipMenuProvider::Extract To',
                label='Extract To',
                tip='',
                icon='')

        submenu.append_item(extract_to_menu_item)
        extract_to_menu_item.connect('activate', self._extract_to, all_files)

        return top_menu_item,
