import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp, QFileDialog, QVBoxLayout, QHBoxLayout, \
    QWidget, QPlainTextEdit, QMessageBox, QDockWidget

from brres import Brres
from autofix import AutoFix
from converters.arg_parse import arg_parse
from converters.convert_dae import DaeConverter2
from converters.convert_obj import ObjConverter
from gui.brres_path import BrresPath
from gui.brres_treeview import BrresTreeView
from gui.converter import ConvertObserver, ConvertManager
from gui.image_manager import ImageManager
from gui.material_browser import MaterialBrowser, MaterialTabs
from gui.poly_editor import PolyEditor
from load_config import load_config, parse_args


class Window(QMainWindow, ConvertObserver):

    def __init__(self, brres_files=[]):
        super().__init__()
        self.open_files = []
        self.brres = None
        ConvertManager.get().subscribe(self)
        self.cwd = os.getcwd()
        AutoFix.get().set_pipe(self)
        self.__init_UI()
        for file in brres_files:
            self.open(file.name)
        self.show()

    def __init_menus(self):
        # Actions
        exit_act = QAction('&Exit', self)
        exit_act.setShortcut('Ctrl+q')
        exit_act.setStatusTip('Exit Application')
        exit_act.triggered.connect(self.close)
        # Open
        open_act = QAction('&Open', self)
        open_act.setShortcut('Ctrl+o')
        open_act.setStatusTip('Open a Brres file')
        open_act.triggered.connect(self.open_dialog)
        # Save
        save_act = QAction('&Save', self)
        save_act.setShortcut('Ctrl+s')
        save_act.setStatusTip('Save file')
        save_act.triggered.connect(self.save)
        # Save as
        save_as = QAction('Save &As', self)
        save_as.setStatusTip('Save file as')
        save_as.triggered.connect(self.save_as_dialog)
        # import
        import_act = QAction('&Import', self)
        import_act.setShortcut('Ctrl+i')
        import_act.setStatusTip('Import file')
        import_act.triggered.connect(self.import_file_dialog)
        # export
        export_act = QAction('&Export', self)
        export_act.setShortcut('Ctrl+e')
        export_act.setStatusTip('Export file')
        export_act.triggered.connect(self.export_file_dialog)
        # File Menu
        menu = self.menuBar()
        fileMenu = menu.addMenu('&File')
        fileMenu.addAction(open_act)
        fileMenu.addAction(save_act)
        fileMenu.addAction(save_as)
        fileMenu.addSeparator()
        fileMenu.addAction(import_act)
        fileMenu.addAction(export_act)
        fileMenu.addSeparator()
        fileMenu.addAction(exit_act)

    def __init_child_UI(self, top_layout):
        # left
        vert_widget = QWidget(self)
        top_layout.addWidget(vert_widget)
        vert_layout = QVBoxLayout()
        vert_widget.setLayout(vert_layout)
        widget = QWidget(self)
        vert_layout.addWidget(widget)
        center_layout = QHBoxLayout()
        widget.setLayout(center_layout)
        self.logger = QPlainTextEdit(self)
        self.logger.setReadOnly(True)
        self.logger.setFixedHeight(100)
        vert_layout.addWidget(self.logger)

        self.treeview = BrresTreeView(self)
        center_layout.addWidget(self.treeview)
        self.poly_editor = PolyEditor(self)
        center_layout.addWidget(self.poly_editor)
        # center_widget.setGeometry(0, 0, 300, 300)

        # right
        # top_layout.addSpacing(30)
        self.material_browser = MaterialTabs(self)
        top_layout.addWidget(self.material_browser)
        # self.material_browser.setFixedWidth(300)

    def __init_UI(self):
        self.setWindowTitle('ANoobs Brres Material Tool')
        self.resize(800, 600)
        self.__init_menus()
        main_layout = QHBoxLayout()
        self.__init_child_UI(main_layout)
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        self.statusBar().showMessage('Ready')

    def on_update_polygon(self, poly):
        self.poly_editor.on_update_polygon(poly)

    def emit(self, message):
        self.logger.appendHtml(message)

    def get_brres_by_fname(self, fname):
        path = os.path.abspath(fname)
        for x in self.open_files:
            if os.path.abspath(x.name) == path:
                return x

    def set_brres(self, brres):
        if brres != self.brres:
            self.brres = brres

    def open_dialog(self):
        fname, filter = QFileDialog.getOpenFileName(self, 'Open file',
                                                    self.cwd, "Brres files (*.brres)")
        if fname:
            self.open(fname)

    def open(self, fname):
        self.cwd = os.path.dirname(fname)
        opened = self.get_brres_by_fname(fname)
        if opened:
            self.set_brres(opened)
        else:
            brres = Brres.get_brres(fname)
            self.set_brres(brres)
            self.open_files.append(brres)
            self.treeview.add_brres_tree(brres)
            self.material_browser.add_brres_materials_to_scene(brres)

    def save(self):
        for x in self.open_files:
            # A precaution against overwriting old models
            overwrite = True if not x.has_new_model else Brres.OVERWRITE
            x.save(overwrite=overwrite)

    def save_as_dialog(self):
        fname, filter = QFileDialog.getSaveFileName(self, 'Save as', self.cwd, 'Brres files (*.brres)')
        if fname:
            self.cwd = os.path.dirname(fname)
            if self.brres:
                self.brres.save(fname, overwrite=True)

    def import_texture(self, filename):
        raise NotImplementedError()

    def import_file(self, fname, brres_name=None, brres=None):
        if brres is None:
            if brres_name is not None:
                brres = self.get_brres_by_fname(brres_name)
            elif self.brres and os.path.splitext(os.path.basename(self.brres.name))[0] == \
                    os.path.splitext(os.path.basename(fname))[0]:
                brres = self.brres
        self.cwd, name = os.path.split(fname)
        base_name, ext = os.path.splitext(name)
        lower = ext.lower()
        if lower == '.dae':
            converter = DaeConverter2(brres, fname)
        elif lower == '.obj':
            converter = ObjConverter(brres, fname)
        # elif lower in ('.png', '.jpg', '.bmp', '.tga'):
        #     return self.import_texture(fname)
        else:
            self.statusBar().showMessage('Unknown extension {}'.format(ext))
            return
        converter.load_model()
        self.on_conversion_finish(converter)
        # ConvertManager.get().enqueue(converter)

    def on_conversion_finish(self, converter):
        self.open(converter.brres.name)

    def import_file_dialog(self, brres=None):
        fname, filter = QFileDialog.getOpenFileName(self, 'Import model', self.cwd, '(*.dae *.obj)')
        if fname:
            self.import_file(fname, brres)

    def export_file_dialog(self, brres=None):
        if brres is None:
            brres = self.brres
        fname, fil = QFileDialog.getSaveFileName(self, 'Export model', self.cwd, 'Model files (*.dae *.obj)')
        if fname:
            self.cwd, name = os.path.split(fname)
            base_name, ext = os.path.splitext(name)
            lower = ext.lower()
            if lower == '.obj':
                converter = ObjConverter(brres, fname, encode=False)
            elif lower == '.dae':
                converter = DaeConverter2(brres, fname, encode=False)
            else:
                self.statusBar().showMessage('Unknown extension {}'.format(ext))
                return
            self.update_status('Added {} to queue'.format(brres.name))
            ConvertManager.enqueue(converter)

    def close_file(self, brres=None):
        if brres is None:
            brres = self.brres
        if brres.is_modified:
            m = QMessageBox(QMessageBox.Warning, 'Save Before Closing',
                            f'Save {brres.name} before closing?',
                            buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=self)
            if m.exec_():
                brres.save(overwrite=True)
        self.open_files.remove(brres)
        brres.close()
        self.brres = None
        self.treeview.on_file_close()

    def shouldExitAnyway(self, result):
        return result == QMessageBox.Ok

    def closeEvent(self, event):
        files_to_save = []
        for x in self.open_files:
            if x.is_modified:
                files_to_save.append(x)
        if files_to_save and not Brres.OVERWRITE:
            self.files_to_save = files_to_save
            fnames = ', '.join([x.name for x in files_to_save])

            m = QMessageBox(QMessageBox.Warning, 'Confirm Exit',
                            f'Exit without saving {fnames}?', buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=self)

            if m.exec_():
                event.accept()
            else:
                event.ignore()
        else:
            for x in files_to_save:
                x.close()
            event.accept()

    def info(self, message):
        self.emit('<p style="color:Blue;">' + message + '</p>')

    def warn(self, message):
        self.emit('<p style="color:Red;">' + message + '</p>')

    def error(self, message):
        self.emit('<p style="color:Red;">' + message + '</p>')

    def update_status(self, message):
        self.statusBar().showMessage(message)


def on_exit():
    #   join other threads
    ImageManager.stop()
    ConvertManager.stop()
    AutoFix.get().quit()


def main():
    argv = sys.argv[1:]
    if getattr(sys, 'frozen', False):
        base_path = sys.executable
    else:
        base_path = os.path.dirname(__file__)
    parse_args(argv, base_path)
    exe = QApplication(argv)
    exe.setStyle('Fusion')
    d = Window()
    result = exe.exec_()
    on_exit()
    sys.exit(result)


if __name__ == '__main__':
    main()
