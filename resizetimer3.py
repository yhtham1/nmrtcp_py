
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

// constructor
MainWindow::MainWindow(QWidget* pParent, Qt::WindowFlags flags) : QMainWindow(pParent, flags)
{
    m_bUserIsResizing = false;
    qApp->installEventFilter(this);
}

// this will be called when any event in the application occurs
bool MainWindow::eventFilter(QObject* pObj, QEvent* pEvent)
{
    // We need to check for both types of mouse release, because it can vary on which type happens when resizing.
    if ((pEvent->type() == QEvent::MouseButtonRelease) || (pEvent->type() == QEvent::NonClientAreaMouseButtonRelease)) {
        QMouseEvent* pMouseEvent = dynamic_cast<QMouseEvent*>(pEvent);
        if ((pMouseEvent->button() == Qt::MouseButton::LeftButton) && m_bUserIsResizing) {
            printf("Gotcha!\n");
            m_bUserIsResizing = false; // reset user resizing flag
        }
    }
    return QObject::eventFilter(pObj, pEvent); // pass it on without eating it
}

// override from QWidget that triggers whenever the user resizes the window
void MainWindow::resizeEvent(QResizeEvent* pEvent) { m_bUserIsResizing = true; }


if __name__ == "__main__":
	app = QApplication(sys.argv)
	win = QMainWindow()
	view = DelayedUpdater()
	win.setCentralWidget(view)
	win.show()
	
	view.delayEnabled = True
	sys.exit(app.exec_())
	
	
	