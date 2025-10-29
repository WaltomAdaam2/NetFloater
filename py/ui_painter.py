from PyQt5.QtGui import QPainter, QPainterPath, QColor, QFont, QIcon, QLinearGradient, QFontMetrics, QPixmap, QPen
from PyQt5.QtCore import Qt, QRectF

class UIPainter:
    def __init__(self):
        self.radius = 16
    
    def create_tray_icon(self):
        """Create system tray icon"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw network traffic icon
        painter.setBrush(QColor(76, 175, 80))  # Download green
        painter.drawEllipse(2, 2, 6, 6)  # Bottom-left dot - download
        
        painter.setBrush(QColor(255, 152, 0))  # Upload orange
        painter.drawEllipse(8, 8, 6, 6)  # Top-right dot - upload
        
        # Connection line
        painter.setPen(QPen(QColor(200, 200, 200, 180), 1))
        painter.drawLine(5, 5, 11, 11)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def paint_background(self, painter, rect):
        """Paint background"""
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self.radius, self.radius)

        # Draw semi-transparent background
        painter.setBrush(QColor(20, 20, 20, 120))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Draw thin white outline
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), self.radius, self.radius)
    
    def paint_full_mode(self, painter, rect, progress, download_anim, upload_anim, show_percentage, download_speed, upload_speed, font_size):
        """Paint full mode"""
        bar_full_width = rect.width() - 30
        bar_height = 12
        
        # Bar container areas
        dl_container_rect = QRectF(rect.left() + 15, rect.top() + 35, bar_full_width, bar_height)
        ul_container_rect = QRectF(rect.left() + 15, rect.top() + 55, bar_full_width, bar_height)
        
        # Actual traffic bar areas
        dl_rect = QRectF(rect.left() + 15, rect.top() + 35, bar_full_width * download_anim, bar_height)
        ul_rect = QRectF(rect.left() + 15, rect.top() + 55, bar_full_width * upload_anim, bar_height)
        
        # Draw container outlines first
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(dl_container_rect, 6, 6)
        painter.drawRoundedRect(ul_container_rect, 6, 6)
        
        # Download bar gradient - green theme
        dl_gradient = QLinearGradient(dl_rect.topLeft(), dl_rect.topRight())
        dl_gradient.setColorAt(0, QColor(76, 175, 80, 220))
        dl_gradient.setColorAt(1, QColor(129, 199, 132, 220))
        
        # Upload bar gradient - orange theme
        ul_gradient = QLinearGradient(ul_rect.topLeft(), ul_rect.topRight())
        ul_gradient.setColorAt(0, QColor(255, 152, 0, 220))
        ul_gradient.setColorAt(1, QColor(255, 183, 77, 220))
        
        # Draw actual traffic bars
        painter.setBrush(dl_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(dl_rect, 6, 6)
        
        painter.setBrush(ul_gradient)
        painter.drawRoundedRect(ul_rect, 6, 6)
        
        # Text display - with opacity gradient
        alpha = int(255 * (1 - progress))
        font = QFont("Segoe UI", max(8, int(font_size * (1 - progress * 0.3))))
        font.setBold(True)
        painter.setFont(font)

        if show_percentage:
            dl_percent = int(download_anim * 100)
            ul_percent = int(upload_anim * 100)
            
            painter.setPen(QColor(76, 175, 80, alpha))
            painter.drawText(rect.left() + 15, rect.top() + 25, f"↓ {dl_percent}%")
            
            painter.setPen(QColor(255, 152, 0, alpha))
            painter.drawText(rect.left() + 15 + rect.width()//2, rect.top() + 25, f"↑ {ul_percent}%")
        else:
            # Format speed text
            if download_speed > 1024:
                dl_text = f"↓ {download_speed/1024:.1f} MB/s"
            else:
                dl_text = f"↓ {download_speed:.1f} KB/s"
                
            if upload_speed > 1024:
                ul_text = f"↑ {upload_speed/1024:.1f} MB/s"
            else:
                ul_text = f"↑ {upload_speed:.1f} KB/s"
            
            painter.setPen(QColor(76, 175, 80, alpha))
            painter.drawText(rect.left() + 15, rect.top() + 25, dl_text)
            
            painter.setPen(QColor(255, 152, 0, alpha))
            upload_x = rect.left() + 15 + rect.width()//2
            painter.drawText(upload_x, rect.top() + 25, ul_text)
    
    def paint_compact_mode(self, painter, rect, download_anim, upload_anim):
        """Paint compact mode - vertical bars"""
        # Vertical bar containers
        bar_width = 12
        bar_max_height = rect.height() - 20
        spacing = 8
        
        # Calculate bar positions
        total_width = bar_width * 2 + spacing
        start_x = (rect.width() - total_width) // 2
        base_y = rect.bottom() - 10
        
        # Bar containers (full range)
        dl_container_rect = QRectF(start_x, base_y - bar_max_height, bar_width, bar_max_height)
        ul_container_rect = QRectF(start_x + bar_width + spacing, base_y - bar_max_height, bar_width, bar_max_height)
        
        # Actual displayed bars (based on traffic)
        dl_height = bar_max_height * download_anim
        dl_rect = QRectF(start_x, base_y - dl_height, bar_width, dl_height)
        
        ul_height = bar_max_height * upload_anim
        ul_rect = QRectF(start_x + bar_width + spacing, base_y - ul_height, bar_width, ul_height)
        
        # Draw container outlines first
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(dl_container_rect, 3, 3)
        painter.drawRoundedRect(ul_container_rect, 3, 3)
        
        # Download vertical bar gradient - light to dark
        dl_gradient = QLinearGradient(dl_rect.topLeft(), dl_rect.bottomLeft())
        dl_gradient.setColorAt(0, QColor(129, 199, 132, 220))  # Light green
        dl_gradient.setColorAt(1, QColor(76, 175, 80, 220))    # Dark green
        
        # Upload vertical bar gradient - light to dark
        ul_gradient = QLinearGradient(ul_rect.topLeft(), ul_rect.bottomLeft())
        ul_gradient.setColorAt(0, QColor(255, 183, 77, 220))   # Light orange
        ul_gradient.setColorAt(1, QColor(255, 152, 0, 220))    # Dark orange
        
        # Draw actual traffic bars
        painter.setBrush(dl_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(dl_rect, 3, 3)
        
        painter.setBrush(ul_gradient)
        painter.drawRoundedRect(ul_rect, 3, 3)
    
    def paint_mode_bars(self, painter, rect, compact_mode, mode_progress, download_anim, upload_anim, show_percentage, download_speed, upload_speed, font_size):
        """Paint mode switching animation bars (unified entry)"""
        if compact_mode or mode_progress > 0.1:
            # Compact mode or switching - show vertical bars
            self.paint_compact_mode(painter, rect, download_anim, upload_anim)
        else:
            # Full mode - show horizontal bars and text
            self.paint_full_mode(painter, rect, mode_progress, download_anim, upload_anim, show_percentage, download_speed, upload_speed, font_size)
    
    def calculate_text_length(self, show_percentage, download_anim, upload_anim, download_speed, upload_speed):
        """Calculate required width for current text"""
        test_font = QFont("Segoe UI", 10)
        metrics = QFontMetrics(test_font)
        
        if show_percentage:
            dl_percent = int(download_anim * 100)
            ul_percent = int(upload_anim * 100)
            text = f"↓ {dl_percent}%  ↑ {ul_percent}%"
        else:
            if download_speed > 1024:
                dl_text = f"↓ {download_speed/1024:.1f} MB/s"
            else:
                dl_text = f"↓ {download_speed:.1f} KB/s"
                
            if upload_speed > 1024:
                ul_text = f"↑ {upload_speed/1024:.1f} MB/s"
            else:
                ul_text = f"↑ {upload_speed:.1f} KB/s"
            
            text = f"{dl_text}  {ul_text}"
        
        return metrics.width(text)