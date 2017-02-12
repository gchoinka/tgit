
import Globals
import Utils
import GitUtils

from PyQt5 import QtWidgets, QtGui, QtCore
import threading
import tempfile

filesListItemColumn_diff = 0
filesListItemColumn_lines = 1
filesListItemColumn_filename = 2
filesListItemColumnCount = 3

def diff_nonblocking( commit, file ):
    file1content = Utils.call( ['git', 'show', '%s~1:%s' % (commit.commitHash, file)], cwd=Globals.repositoryDir )
    file2content = Utils.call( ['git', 'show', '%s:%s' % (commit.commitHash, file)], cwd=Globals.repositoryDir )
    file1 = tempfile.NamedTemporaryFile( mode='w', suffix='_OLD_%s' % os.path.basename(file) )
    file2 = tempfile.NamedTemporaryFile( mode='w', suffix='_NEW_%s' % os.path.basename(file) )
    file1.write( '\n'.join( file1content ) )
    file2.write( '\n'.join( file2content ) )
    file1.flush()
    file2.flush()
    Utils.call( ['meld', file1.name, file2.name], cwd=Globals.repositoryDir )

@QtCore.pyqtSlot()
def on_filesList_itemSelectionChanged():
    items = Globals.ui_filesList.selectedItems()
    if items:
        files = list( map( lambda item: item.text( filesListItemColumn_filename ), items ) )
        Globals.ui_diffViewer.setHtml( GitUtils.getDiffHtml( Globals.selectedCommit.commitHash, files ) )

        if Globals.calculateDiffHashes and len( items ) == 1:
            item = items[0]
            if not item.text( filesListItemColumn_diff ):
                diffHash = GitUtils.getDiffHash( Globals.selectedCommit.commitHash, files, forceGeneration=True )
                item.setText( filesListItemColumn_diff, diffHash )

@QtCore.pyqtSlot( QtWidgets.QListWidgetItem )
def on_filesList_itemActivated( item ):
    file = item.text( filesListItemColumn_filename )
    thread = threading.Thread( target=diff_nonblocking, args=(Globals.selectedCommit, file) )
    thread.start()

@QtCore.pyqtSlot( QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidgetItem )
def on_filesList_currentItemChanged( current, before ):
    """
    :type current: QtWidgets.QTreeWidgetItem
    :type before: QtWidgets.QTreeWidgetItem
    """
    Globals.ui_followViewerScrollArea.setVisible( bool( current ) )
    if current:
        filename = current.text(filesListItemColumn_filename)
        hashes = Globals.selectedCommit.getHistory( filename )
        htmls = ['<strong>history:</strong> (<a href="history:%s:%s">new window</a>)<br />' % (Globals.selectedCommit.commitHash, filename)]
        htmls.extend( '<br />'.join( map( lambda c: c.getOnelinerHtml( True, filename ), map( lambda h: Globals.allCommitsHash[h], hashes ) ) ) )
        Globals.ui_followViewer.setText( '' )
        QtCore.QCoreApplication.processEvents( QtCore.QEventLoop.ExcludeUserInputEvents ) # dirty workaround to avoid scrolling
        Globals.ui_followViewer.setText( ''.join( htmls ) )
