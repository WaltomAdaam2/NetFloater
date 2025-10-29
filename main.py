import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, pyqtProperty, QSize

from py.config_manager import ConfigManager
from py.network_monitor import NetworkMonitor
from py.auto_start_manager import AutoStartManager
from py.ui_painter import UIPainter

class FloaterWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.radius = 16
        self.is_dragging = False
        self.offset = QPoint()
        
        # 初始化管理器
        self.config_manager = ConfigManager()
        self.network_monitor = NetworkMonitor()
        self.auto_start_manager = AutoStartManager()
        self.ui_painter = UIPainter()
        
        # 从配置中加载设置
        self.show_percentage = self.config_manager.get('show_percentage', False)
        self.window_position = self.config_manager.get('window_position', None)
        self.auto_start = self.config_manager.get('auto_start', False)
        self.compact_mode = self.config_manager.get('compact_mode', False)
        
        print(f"Loaded config: compact_mode = {self.compact_mode}")
        
        # 网络速度
        self.download_speed = 0.0
        self.upload_speed = 0.0
        
        # 动画值
        self._download_animation = 0.0
        self._upload_animation = 0.0
        
        # 字体大小自适应
        self.current_font_size = 10
        
        # 自动吸附动画
        self.snap_anim = QPropertyAnimation(self, b"pos")
        self.snap_anim.setDuration(300)
        
        # 拖动时透明度
        self.drag_opacity = 1.0
        
        # 模式切换动画
        self.mode_progress = 1.0 if self.compact_mode else 0.0
        self.mode_anim_target = 1.0 if self.compact_mode else 0.0
        self.mode_anim_timer = QTimer(self)
        self.mode_anim_timer.timeout.connect(self.updateModeAnimation)
        self.mode_anim_timer.start(50)

        self.initUI()
        self.initTimers()
        self.initTray()
        
        # 设置窗口位置
        self.setWindowPosition()

    def setWindowPosition(self):
        """Set window position"""
        if self.window_position:
            x = self.window_position.get('x')
            y = self.window_position.get('y')
            
            # Check if position is within screen bounds
            screen = QApplication.primaryScreen().availableGeometry()
            if (0 <= x <= screen.width() - self.width() and 
                0 <= y <= screen.height() - self.height()):
                self.move(x, y)
                return
        
        # If no saved position or invalid, use default position (right center)
        self.setToRightCenter()

    def setToRightCenter(self):
        """Set window to right center of screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        if self.compact_mode:
            width = 60
        else:
            width = 220
        x = screen.right() - width
        y = (screen.height() - 80) // 2
        self.move(x, y)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if self.compact_mode:
            self.resize(60, 80)
        else:
            self.resize(220, 80)
            
        self.setStyleSheet("background: transparent;")
        self.show()

    def initTimers(self):
        # Main timer - update speed
        self.speed_timer = QTimer(self)
        self.speed_timer.timeout.connect(self.updateSpeed)
        self.speed_timer.start(1000)
        
        # Animation timer - smoother traffic bars
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.updateAnimation)
        self.animation_timer.start(50)

    def toggle_auto_start(self):
        """Toggle auto-start on boot"""
        if self.auto_start_manager.is_enabled():
            self.auto_start_manager.disable()
            self.auto_start = False
        else:
            self.auto_start_manager.enable()
            self.auto_start = True
        
        self.auto_start_action.setChecked(self.auto_start)
        self.config_manager.set('auto_start', self.auto_start)

    def initTray(self):
        tray_icon = self.ui_painter.create_tray_icon()
        self.tray = QSystemTrayIcon(tray_icon)
        self.tray.setToolTip("Network Traffic Monitor")
        self.tray.setVisible(True)

        menu = QMenu()
        
        # Auto-start option
        self.auto_start_action = QAction("Start with Windows", self)
        self.auto_start_action.setCheckable(True)
        self.auto_start_action.setChecked(self.auto_start_manager.is_enabled())
        self.auto_start_action.triggered.connect(self.toggle_auto_start)
        
        # Display mode toggle
        self.toggle_display_action = QAction("Show Percentage", self)
        self.toggle_display_action.triggered.connect(self.toggleDisplayMode)
        
        # Window mode toggle
        mode_text = "Switch to Compact Mode" if not self.compact_mode else "Switch to Full Mode"
        self.toggle_mode_action = QAction(mode_text, self)
        self.toggle_mode_action.triggered.connect(self.toggleWindowMode)
        
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggleVisible)
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quitApplication)
        
        menu.addAction(self.auto_start_action)
        menu.addAction(self.toggle_display_action)
        menu.addAction(self.toggle_mode_action)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray)

    def toggleWindowMode(self):
        """Toggle window mode (smooth animation + bounce)"""
        # Save current precise snap position
        screen = QApplication.primaryScreen().availableGeometry()
        current_x = self.x()
        current_y = self.y()
        current_width = self.width()
        
        # Calculate which side it's snapped to
        is_left_adsorbed = abs(current_x - screen.left()) < 10
        is_right_adsorbed = abs(current_x + current_width - screen.right()) < 10
        
        # Save vertical position info
        is_top_adsorbed = abs(current_y - screen.top()) < 10
        is_bottom_adsorbed = abs(current_y + self.height() - screen.bottom()) < 10
        
        # Toggle mode
        self.compact_mode = not self.compact_mode
        self.toggle_mode_action.setText("Switch to Compact Mode" if not self.compact_mode else "Switch to Full Mode")
        
        # Immediately save mode setting to config
        self.config_manager.set('compact_mode', self.compact_mode)
        print(f"Saved mode setting: compact_mode = {self.compact_mode}")
        
        # Animate window resize
        start_size = self.size()
        end_size = QSize(60, 80) if self.compact_mode else QSize(220, 80)

        self.size_anim = QPropertyAnimation(self, b"size")
        self.size_anim.setDuration(300)
        self.size_anim.setStartValue(start_size)
        self.size_anim.setEndValue(end_size)
        self.size_anim.start()

        # Set mode gradient target for drawing opacity
        self.mode_anim_target = 1.0 if self.compact_mode else 0.0

        # Save snap info for repositioning after animation
        self.adsorb_info = {
            'is_left_adsorbed': is_left_adsorbed,
            'is_right_adsorbed': is_right_adsorbed,
            'is_top_adsorbed': is_top_adsorbed,
            'is_bottom_adsorbed': is_bottom_adsorbed,
            'current_x': current_x,
            'current_y': current_y,
            'current_width': current_width
        }

        # Execute snap and bounce after animation
        self.size_anim.finished.connect(self.snapAndBounce)

    def snapAndBounce(self):
        """Maintain snap position and add slight bounce after resize"""
        screen = QApplication.primaryScreen().availableGeometry()
        info = self.adsorb_info
        
        # Reposition based on previous snap state
        if info['is_right_adsorbed']:
            new_x = screen.right() - self.width()
            if info['is_top_adsorbed']:
                new_y = screen.top()
            elif info['is_bottom_adsorbed']:
                new_y = screen.bottom() - self.height()
            else:
                new_y = info['current_y']
                
        elif info['is_left_adsorbed']:
            new_x = screen.left()
            if info['is_top_adsorbed']:
                new_y = screen.top()
            elif info['is_bottom_adsorbed']:
                new_y = screen.bottom() - self.height()
            else:
                new_y = info['current_y']
        else:
            if self.compact_mode:
                new_x = info['current_x'] + (info['current_width'] - self.width())
            else:
                new_x = info['current_x']
            
            if info['is_top_adsorbed']:
                new_y = screen.top()
            elif info['is_bottom_adsorbed']:
                new_y = screen.bottom() - self.height()
            else:
                new_y = info['current_y']
        
        # Move to new position
        self.move(new_x, new_y)
        
        # Bounce animation
        end_pos = self.pos()
        self.bounce_anim = QPropertyAnimation(self, b"pos")
        self.bounce_anim.setDuration(150)
        self.bounce_anim.setKeyValueAt(0, end_pos)
        self.bounce_anim.setKeyValueAt(0.5, end_pos - QPoint(0, 8))
        self.bounce_anim.setKeyValueAt(1, end_pos)
        self.bounce_anim.start()

    def updateModeAnimation(self):
        """Update mode switch animation"""
        target = self.mode_anim_target
        self.mode_progress = self.mode_progress * 0.7 + target * 0.3
        self.update()

    @pyqtProperty(float)
    def drag_opacity(self):
        return self._drag_opacity

    @drag_opacity.setter
    def drag_opacity(self, value):
        self._drag_opacity = value
        self.setWindowOpacity(value)

    def toggleDisplayMode(self):
        self.show_percentage = not self.show_percentage
        self.toggle_display_action.setText("Show Percentage" if self.show_percentage else "Show Units")
        self.config_manager.set('show_percentage', self.show_percentage)
        self.update()

    def on_tray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def toggleVisible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.setToRightCenter()

    def quitApplication(self):
        """Exit application"""
        # Save current position
        self.config_manager.set('window_position', {
            'x': self.x(),
            'y': self.y()
        })
        # Ensure mode setting is saved
        self.config_manager.set('compact_mode', self.compact_mode)
        # Save other settings
        self.config_manager.set('show_percentage', self.show_percentage)
        self.config_manager.set('auto_start', self.auto_start)
        
        print(f"Saved config on exit: compact_mode = {self.compact_mode}")
        QApplication.quit()

    def updateSpeed(self):
        self.network_monitor.update_speed()
        speeds = self.network_monitor.get_speeds()
        self.download_speed = speeds['download']
        self.upload_speed = speeds['upload']

    def updateAnimation(self):
        # Smooth animation transition
        target_dl = min(self.download_speed / 512, 1.0)
        target_ul = min(self.upload_speed / 512, 1.0)
        
        self._download_animation = self._download_animation * 0.7 + target_dl * 0.3
        self._upload_animation = self._upload_animation * 0.7 + target_ul * 0.3
        
        # Font size adaptation in full mode
        if not self.compact_mode:
            text_length = self.calculateTextLength()
            available_width = self.width() - 30
            target_font_size = 10
            
            if text_length > available_width:
                scale_factor = available_width / text_length
                target_font_size = max(8, 10 * scale_factor)
            
            self.current_font_size = self.current_font_size * 0.8 + target_font_size * 0.2
        
        self.update()

    def calculateTextLength(self):
        """Calculate required width for current text"""
        from PyQt5.QtGui import QFont, QFontMetrics
        
        test_font = QFont("Segoe UI", 10)
        metrics = QFontMetrics(test_font)
        
        if self.show_percentage:
            dl_percent = int(self._download_animation * 100)
            ul_percent = int(self._upload_animation * 100)
            text = f"↓ {dl_percent}%  ↑ {ul_percent}%"
        else:
            dl_text, ul_text = self.network_monitor.get_formatted_speeds()
            text = f"{dl_text}  {ul_text}"
        
        return metrics.width(text)

    # --- Mouse Events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.offset = event.pos()
            self.snap_anim.stop()
            self.drag_opacity = 0.7

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.drag_opacity = 1.0
            self.snapToEdge()
            self.config_manager.set('window_position', {
                'x': self.x(),
                'y': self.y()
            })

    def mouseDoubleClickEvent(self, event):
        """Double click to toggle window mode"""
        if event.button() == Qt.LeftButton:
            self.toggleWindowMode()

    # --- Painting ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        
        # Draw background
        self.ui_painter.paint_background(painter, rect)
        
        # Draw mode content
        if self.compact_mode or self.mode_progress > 0.1:
            # Compact mode or switching - show vertical bars
            self.ui_painter.paint_compact_mode(painter, rect, self._download_animation, self._upload_animation)
        else:
            # Full mode - show horizontal bars and text
            self.ui_painter.paint_full_mode(
                painter, rect, self.mode_progress, 
                self._download_animation, self._upload_animation,
                self.show_percentage, self.download_speed, self.upload_speed,
                self.current_font_size
            )

    # --- Auto Snap ---
    def snapToEdge(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x, y = self.x(), self.y()
        w, h = self.width(), self.height()
        
        # Calculate distances to edges
        left_distance = abs(x - screen.left())
        right_distance = abs(screen.right() - (x + w))
        top_distance = abs(y - screen.top())
        bottom_distance = abs(screen.bottom() - (y + h))
        
        # Find closest horizontal edge
        if left_distance < right_distance and left_distance < 100:
            target_x = screen.left()
        elif right_distance < 100:
            target_x = screen.right() - w
        else:
            target_x = x
        
        # Vertical snap
        if top_distance < 50:
            target_y = screen.top()
        elif bottom_distance < 50:
            target_y = screen.bottom() - h
        else:
            target_y = y

        self.snap_anim.stop()
        self.snap_anim.setStartValue(self.pos())
        self.snap_anim.setEndValue(QPoint(target_x, target_y))
        self.snap_anim.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    floater = FloaterWidget()
    sys.exit(app.exec_())