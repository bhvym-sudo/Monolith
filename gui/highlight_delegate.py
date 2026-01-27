from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QTextDocument, QAbstractTextDocumentLayout, QPainter


class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_term = ""
    
    def set_search_term(self, term):
        self.search_term = term.lower()
    
    def paint(self, painter, option, index):
        # Highlight column 1 (value column)
        text = index.data(Qt.DisplayRole)
        if not text or not self.search_term:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.color(QPalette.Highlight))
        else:
            painter.fillRect(option.rect, option.palette.color(QPalette.Base))
        
        # Setup text drawing
        painter.setPen(option.palette.color(QPalette.Text))
        
        # Find and highlight matches
        text_lower = text.lower()
        x = option.rect.x() + 5
        y = option.rect.y() + option.rect.height() // 2 + 5
        
        start = 0
        while True:
            idx = text_lower.find(self.search_term, start)
            if idx == -1:
                # Draw remaining text
                painter.drawText(x, y, text[start:])
                break
            
            # Draw text before match
            before_text = text[start:idx]
            painter.drawText(x, y, before_text)
            x += painter.fontMetrics().horizontalAdvance(before_text)
            
            # Draw matched text with yellow background
            matched_text = text[idx:idx+len(self.search_term)]
            match_width = painter.fontMetrics().horizontalAdvance(matched_text)
            
            # Fill yellow background
            painter.fillRect(x, option.rect.y() + 2, match_width, option.rect.height() - 4, Qt.yellow)
            
            # Draw black text on yellow
            painter.setPen(Qt.black)
            painter.drawText(x, y, matched_text)
            painter.setPen(option.palette.color(QPalette.Text))
            
            x += match_width
            start = idx + len(self.search_term)
        
        painter.restore()
    
    def sizeHint(self, option, index):
        return super().sizeHint(option, index)
