#!/usr/bin/env python2
#encoding: utf-8
import requests
import lxml.html
import os.path
from io import BytesIO

class CancelledError(Exception):
    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return self.msg

    __repr__ = __str__

class BufferReader(BytesIO):
    def __init__(self, buf=b'',
                 callback=None,
                 cb_args=(),
                 cb_kwargs={}):
        self._callback = callback
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs
        self._progress = 0
        self._len = len(buf)
        BytesIO.__init__(self, buf)

    def __len__(self):
        return self._len

    def read(self, n=-1):
        chunk = BytesIO.read(self, n)
        self._progress += int(len(chunk))
        self._cb_kwargs.update({
            'size'    : self._len,
            'progress': self._progress
        })
        if self._callback:
            try:
                self._callback(*self._cb_args, **self._cb_kwargs)
            except: # catches exception from the callback
                raise CancelledError('The upload was cancelled.')
        return chunk

session = requests.session()

class Uploader(object):
    url = "http://lasana.rufian.eu/"

    def __init__(self, session=session):
        self.session = session
        self.initialized = False

    def initialize(self):
        if not self.initialized:
            response = requests.get(self.url)
            self.cookies = {
                'csrftoken': response.cookies['csrftoken'],
                }

    def upload(self, filename, progress):
        self.initialize()

        files = {"file": (os.path.basename(filename), open(filename, 'rb').read()),
                 "expires_in": "360",
                 "csrfmiddlewaretoken": self.cookies["csrftoken"]}

        (data, ctype) = requests.packages.urllib3.filepost.encode_multipart_formdata(files)

        headers = {
            "Content-Type": ctype
        }

        body = BufferReader(data, progress)
        response = self.session.post(self.url, cookies=self.cookies, data=body, headers=headers)

        html = lxml.html.fromstring(response.content)
        link = html.cssselect('#lasagna_url_field')[0].get('value')
        return link


from PyQt4 import Qt, QtCore, QtGui
from . resources import icons_rc


def set_clipboard(content):
    if os.name == 'posix':
        # For linux
        import subprocess
        command = 'xclip -i -selection clipboard'
        xclip = subprocess.Popen(command.split(), stdin=subprocess.PIPE)
        xclip.communicate(content.encode('utf-8'))
        xclip.wait()
    else:
        # For Windows
        Qt.QApplication.instance().clipboard().setText(content)


class UploaderQThread(QtCore.QThread):
    partUploaded = QtCore.pyqtSignal(int, int)
    done = QtCore.pyqtSignal(str)

    def __init__(self, uploader, filename):
        super(UploaderQThread, self).__init__()

        self.uploader = uploader
        self.filename = filename

    def emit_partUploaded(self, size, progress):
        self.partUploaded.emit(size, progress)

    def run(self):
        link = self.uploader.upload(self.filename, self.emit_partUploaded)
        self.done.emit(link)

class QUploader(object):
    def __init__(self, uploader):
        self.uploader = uploader

    def copy_and_close(self):
        self.line_link.selectAll()
        set_clipboard(unicode(self.line_link.text()))
        self.window.close()

    def start_upload(self, filename):
        self.window = QtGui.QWidget()
        self.window.setWindowTitle(u'Lasaña')
        self.window.setWindowIcon(QtGui.QIcon(':/icon.png'))

        self.layout = QtGui.QVBoxLayout()
        self.window.setLayout(self.layout)

        self.progbar = QtGui.QProgressBar()
        self.progbar.setMinimumWidth(500)
        self.layout.addWidget(self.progbar)

        pixmap = QtGui.QPixmap(filename)
        if not pixmap.isNull():
            maxsize = 400
            realsize = max(pixmap.size().width(), pixmap.size().height())
            if realsize < maxsize:
                maxsize = realsize

            self.picture = QtGui.QLabel()
            self.picture.setAlignment(QtCore.Qt.AlignCenter)
            self.picture.setPixmap(pixmap.scaled(maxsize, maxsize,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation))
            self.layout.addWidget(self.picture)
        else:
            self.picture = None

        self.window.adjustSize()
        self.window.move(Qt.QApplication.desktop().screen().rect().center() - self.window.rect().center())
        self.window.show()

        self.uploader_thread = UploaderQThread(self.uploader, filename)
        self.uploader_thread.partUploaded.connect(self.progress)
        self.uploader_thread.done.connect(self.done)
        self.uploader_thread.start()

    def progress(self, size=None, progress=None):
        self.progbar.setMaximum(size)
        self.progbar.setValue(progress)
        if progress == size:
            self.progbar.setFormat("Aceptando archivo...")

    def done(self, link):
        # Close HTTP connection
        self.uploader.session.close()
        
        self.line_link = QtGui.QLineEdit()
        self.line_link.setReadOnly(True)
        self.line_link.setAlignment(QtCore.Qt.AlignCenter)
        font = QtGui.QFont(self.line_link.font())
        font.setPixelSize(23)
        self.line_link.setFont(font)
        self.line_link.setText(link)
        self.line_link.selectAll()
        self.line_link.returnPressed.connect(self.copy_and_close)

        self.progbar.setVisible(False)
        self.layout.removeWidget(self.progbar)
        self.layout.insertWidget(0, self.line_link)
        self.line_link.setFocus()

        return link

def main():
    import os
    import sys
    if os.name == 'nt':
        from . import win32_unicode_argv
    import argparse
    from PyQt4 import Qt, QtGui
    
    if os.name == 'nt':
        # Sets this process as an 'Application User Model' on Windows 7+
        # This is required for icons to work in the taskbar, instead of being
        # replaced by python interpreter icon.
        import ctypes
        myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        

    parser = argparse.ArgumentParser(
            description='Upload files to Lasaña.')
    parser.add_argument('filename', nargs='?')

    args = parser.parse_args()
    qapp = Qt.QApplication(sys.argv)

    if args.filename is not None:
        # This would be easier in Python 3...
        if os.name == 'nt':
            # Already did the trick to convert argv to unicode
            filename = args.filename
        else:
            # Didn't...
            filename = args.filename.decode(sys.getfilesystemencoding())
    else:
        dialog = QtGui.QFileDialog()
        dialog.setWindowTitle(u"Subir un archivo a Lasaña")
        dialog.setWindowIcon(QtGui.QIcon(':/icon.png'))
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        dialog.exec_()

        if len(dialog.selectedFiles()) > 0:
            filename = unicode(dialog.selectedFiles()[0])
        else:
            sys.exit(1)

    quploader = QUploader(Uploader())
    quploader.start_upload(filename)
    qapp.exec_()

if __name__ == "__main__":
    main()
