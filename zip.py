"""Provides ZipFile extract and compress options to Caja context menu."""

import threading
import time
import os

from zipfile import ZipFile

from gi.repository import Caja, GLib, GObject, Gtk


class ProgressBar(Gtk.Window):
    """Window for the progress bar."""
    def __init__(self, path, files, action, target_path=''):
        """Initializes the progress bar."""
        super().__init__(
                title='Progress..', default_height=50, default_width=300)
        self.connect('destroy', Gtk.main_quit)

        # Variables
        self._path = path
        self._files = files
        self._action = action
        self._target_path = target_path

        # Widgets
        self._progress = Gtk.ProgressBar(show_text=True)
        self.add(self._progress)

        # Thread targets
        if action == 'Extracting':
            self._thread = threading.Thread(target=self._extract)
        elif action == 'Compressing':
            self._thread = threading.Thread(target=self._compress)

    def _update_progress(self, data):
        """Updates the progress bar."""
        self._progress.set_text(data['status'])
        self._progress.set_fraction(data['fraction'])

        return False

    def _extract(self):
        """Extract files and provide target for progress bar."""
        total = len(self._files)
        for i, file in enumerate(self._files):
            # Form full path name
            name = file.get_name()
            file_name = os.path.join(self._path, name)

            # Status description
            percentage_as_float = float(i / total)
            percentage = int(percentage_as_float * 100)
            text = f'{self._action} {name}   {percentage}%   ({i}/{total})'
            data = {'status': text, 'fraction': percentage_as_float}
            GLib.idle_add(self._update_progress, data)

            if file_name.endswith('.zip'):
                with ZipFile(file_name, 'r') as zip:
                    if not self._target_path:
                        zip.extractall()
                    else:
                        zip.extractall(self._target_path)

            time.sleep(0.2)

        text = f'{self._action} completed.. 100% {total}/{total}'
        completed = {
            'status': text,
            'fraction': 1.0
        }
        GLib.idle_add(self._update_progress, completed)
        self.destroy()

    def _compress(self):
        """Compress files and provide target for progress bar."""
        all_files = []
        for item in self._files:
            if item.is_directory():
                for root, directories, files in os.walk(item.get_name()):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        all_files.append(filepath)
            else:
                all_files.append(item.get_name())

        total = len(all_files)
        with ZipFile(self._target_path, 'w') as zip:
            for i, file in enumerate(all_files):
                # Status description
                name = os.path.basename(file)
                percentage_as_float = float(i / total)
                percentage = int(percentage_as_float * 100)
                text = f'{self._action} {name}   {percentage}%   ({i}/{total})'
                data = {'status': text, 'fraction': percentage_as_float}
                GLib.idle_add(self._update_progress, data)
                zip.write(file)

                time.sleep(0.2)

        text = f'{self._action} completed.. 100% {total}/{total}'
        completed = {
            'status': text,
            'fraction': 1.0
        }
        GLib.idle_add(self._update_progress, completed)
        self.destroy()

    def start(self):
        """Start the progress bar."""
        self.show_all()
        self._thread.daemon = True
        self._thread.start()


def select_folder():
    """Dialog box for choosing a directory to extract to."""
    action = Gtk.FileChooserAction.SELECT_FOLDER
    dialog = Gtk.FileChooserDialog(
            'Select..',
            None,
            action,
            ('Cancel', Gtk.ResponseType.CANCEL, 'Ok', Gtk.ResponseType.OK)
        )

    dialog.connect('destroy', Gtk.main_quit)
    response = dialog.run()
    directory = ''
    if response == Gtk.ResponseType.OK:
        directory = dialog.get_filename()

    dialog.destroy()
    return directory


def create_file():
    """Dialog box for saving a file."""
    action = Gtk.FileChooserAction.SAVE
    dialog = Gtk.FileChooserDialog(
            'Save as..',
            None,
            action,
            ('Cancel', Gtk.ResponseType.CANCEL, 'Save', Gtk.ResponseType.OK)
        )

    dialog.connect('destroy', Gtk.main_quit)
    dialog.set_current_name('Untitled.zip')

    response = dialog.run()
    file = ''
    if response == Gtk.ResponseType.OK:
        file = dialog.get_filename()

    dialog.destroy()
    return file


class ZipFileMenuProvider(GObject.GObject, Caja.MenuProvider):
    """Context menu for commands."""
    def _extract_here(self, menu, files):
        """Extracts selected files to current location."""
        # Change to current directory to extract here
        path = os.path.dirname(files[0].get_location().get_path())
        os.chdir(path)

        # Commence extraction and progress bar
        progress = ProgressBar(path, files, 'Extracting')
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
            progress = ProgressBar(path, files, 'Extracting', directory)
            progress.start()
            Gtk.main()

    def _compress(self, menu, files):
        """Compress selected files to current directory."""
        file = create_file()
        if file:
            # Get current directory forming full path name
            path = os.path.dirname(files[0].get_location().get_path())
            os.chdir(path)

            # Commence extraction and progress
            progress = ProgressBar(path, files, 'Compressing', file)
            progress.start()
            Gtk.main()

    def get_file_items(self, window, files):
        """Gets files selected and connects functions."""
        # Important to get copy since selecting a file during extraction
        # changes list of files and locks up the instance of Caja
        all_files = files.copy()

        # Set up the top menu with a submenu
        top_menu_item = Caja.MenuItem(
                name='ZipFileMenuProvider::Unzip',
                label='ZipFile Menu',
                tip='',
                icon='')

        submenu = Caja.Menu()
        top_menu_item.set_submenu(submenu)

        # Setup the extract here command
        extract_here_menu_item = Caja.MenuItem(
                name='ZipFileMenuProvider::Extract Here',
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
                name='ZipFileMenuProvider::Extract To',
                label='Extract To',
                tip='',
                icon='')

        submenu.append_item(extract_to_menu_item)
        extract_to_menu_item.connect('activate', self._extract_to, all_files)

        # Setup the compress here command
        extract_to_menu_item = Caja.MenuItem(
                name='ZipFileMenuProvider::Compress Here',
                label='Compress',
                tip='',
                icon='')

        submenu.append_item(extract_to_menu_item)
        extract_to_menu_item.connect(
                'activate',
                self._compress,
                all_files)

        return top_menu_item,
