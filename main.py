import sys
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, pyqtProperty, QSize, QVariantAnimation

from src.config_manager import ConfigManager
from src.network_monitor import NetworkMonitor
from src.auto_start_manager import AutoStartManager
from src.ui_painter import UIPainter
from src.language_manager import LanguageManager

class FloaterWidget(QWidget):
    def __init__(self):
        super().__init__()

        # -------------------- Window & Drag --------------------
        self.radius = 16
        self.is_dragging = False
        self.offset = QPoint()

        # -------------------- Managers --------------------
        self.config_manager = ConfigManager()
        self.network_monitor = NetworkMonitor()
        self.auto_start_manager = AutoStartManager()
        self.ui_painter = UIPainter()
        self.language_manager = LanguageManager(self.config_manager)

        # -------------------- Settings --------------------
        self.show_percentage = self.config_manager.get('show_percentage', False)
        self.window_position = self.config_manager.get('window_position', None)
        self.auto_start = self.config_manager.get('auto_start', False)
        self.compact_mode = self.config_manager.get('compact_mode', False)

        # -------------------- Network Speeds --------------------
        self.download_speed = 0.0
        self.upload_speed = 0.0
        self._download_animation = 0.0
        self._upload_animation = 0.0

        # -------------------- Animations --------------------
        self.current_font_size = 10
        self.snap_anim = QPropertyAnimation(self, b"pos")
        self.snap_anim.setDuration(300)
        self._drag_opacity = 1.0
        self.drag_opacity = 1.0

        # Mode switch animation
        self.mode_progress = 1.0 if self.compact_mode else 0.0
        self.mode_anim_target = 1.0 if self.compact_mode else 0.0
        self.mode_anim_timer = QTimer(self)
        self.mode_anim_timer.timeout.connect(self.updateModeAnimation)
        self.mode_anim_timer.start(50)

        # Fade animation for smooth mode switch
        self._mode_opacity = 1.0

        # -------------------- Init UI --------------------
        self.initUI()
        self.initTimers()
        self.initTray()
        self.setWindowPosition()
        self.language_manager.language_changed.connect(self.on_language_changed)

    # -------------------- Language --------------------
    def on_language_changed(self):
        """Update tray menu when language changes"""
        self.updateTrayMenu()
        self.update()

    def updateTrayMenu(self):
        """Refresh tray menu texts"""
        self.auto_start_action.setText(self.language_manager.tr('start_with_windows'))
        self.toggle_display_action.setText(self.language_manager.tr('show_percentage'))
        self.show_action.setText(self.language_manager.tr('show_hide'))
        self.quit_action.setText(self.language_manager.tr('exit'))
        self.language_menu.setTitle(self.language_manager.tr('language'))

        current_lang = self.language_manager.current_lang
        for action in self.language_actions:
            action.setChecked(action.data() == current_lang)

    # -------------------- Window Position --------------------
    def setWindowPosition(self):
        """Set initial window position with DPI awareness"""
        if self.window_position:
            x = self.window_position.get('x')
            y = self.window_position.get('y')
            screen = QApplication.primaryScreen().availableGeometry()
            if (0 <= x <= screen.width() - self.width() and
                0 <= y <= screen.height() - self.height()):
                self.move(x, y)
                return
        self.setToRightCenter()

    def setToRightCenter(self):
        """Place window to right center of the screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        width, height = (60, 110) if self.compact_mode else (220, 80)
        x = screen.right() - width
        y = (screen.height() - height) // 2
        self.move(x, y)

    # -------------------- UI & Timers --------------------
    def initUI(self):
        """Initialize window UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(60, 110) if self.compact_mode else self.resize(220, 80)
        self.setStyleSheet("background: transparent;")
        self.show()

    def initTimers(self):
        """Initialize network and animation timers"""
        self.speed_timer = QTimer(self)
        self.speed_timer.timeout.connect(self.updateSpeed)
        self.speed_timer.start(1000)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.updateAnimation)
        self.animation_timer.start(50)

    # -------------------- System Tray --------------------
    def toggle_auto_start(self):
        """Toggle auto-start on system boot"""
        if self.auto_start_manager.is_enabled():
            self.auto_start_manager.disable()
            self.auto_start = False
        else:
            self.auto_start_manager.enable()
            self.auto_start = True
        self.auto_start_action.setChecked(self.auto_start)
        self.config_manager.set('auto_start', self.auto_start)

    def initTray(self):
        """Initialize system tray icon and menu"""
        tray_icon = self.ui_painter.create_tray_icon()
        self.tray = QSystemTrayIcon(tray_icon)
        self.tray.setToolTip(self.language_manager.tr('network_traffic_monitor'))
        self.tray.setVisible(True)

        menu = QMenu()
        self.auto_start_action = QAction(self.language_manager.tr('start_with_windows'), self)
        self.auto_start_action.setCheckable(True)
        self.auto_start_action.setChecked(self.auto_start_manager.is_enabled())
        self.auto_start_action.triggered.connect(self.toggle_auto_start)

        self.toggle_display_action = QAction(self.language_manager.tr('show_percentage'), self)
        self.toggle_display_action.triggered.connect(self.toggleDisplayMode)

        self.language_menu = QMenu(self.language_manager.tr('language'))
        self.language_actions = []
        for lang_code, lang_name in self.language_manager.get_available_languages():
            action = QAction(lang_name, self)
            action.setCheckable(True)
            action.setChecked(lang_code == self.language_manager.current_lang)
            action.setData(lang_code)
            action.triggered.connect(lambda checked, code=lang_code: self.switch_language(code))
            self.language_menu.addAction(action)
            self.language_actions.append(action)

        self.show_action = QAction(self.language_manager.tr('show_hide'), self)
        self.show_action.triggered.connect(self.toggleVisible)

        self.quit_action = QAction(self.language_manager.tr('exit'), self)
        self.quit_action.triggered.connect(self.quitApplication)

        menu.addAction(self.auto_start_action)
        menu.addAction(self.toggle_display_action)
        menu.addMenu(self.language_menu)
        menu.addAction(self.show_action)
        menu.addAction(self.quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray)

    def switch_language(self, lang_code):
        """Switch application language"""
        self.language_manager.set_language(lang_code)

    # -------------------- Mode Toggle with Animation --------------------
    def toggleWindowMode(self):
        """Toggle between compact and full mode with smooth animation and bounce"""
        if hasattr(self, 'size_anim') and self.size_anim.state() == QPropertyAnimation.Running:
            return

        screen = QApplication.primaryScreen().availableGeometry()
        current_x, current_y, current_width = self.x(), self.y(), self.width()
        is_left_adsorbed = abs(current_x - screen.left()) < 10
        is_right_adsorbed = abs(current_x + current_width - screen.right()) < 10
        is_top_adsorbed = abs(current_y - screen.top()) < 10
        is_bottom_adsorbed = abs(current_y + self.height() - screen.bottom()) < 10

        self.compact_mode = not self.compact_mode
        self.config_manager.set('compact_mode', self.compact_mode)

        # -------------------- Size Animation --------------------
        start_size = self.size()
        end_size = QSize(60, 110) if self.compact_mode else QSize(220, 80)
        self.size_anim = QPropertyAnimation(self, b"size")
        self.size_anim.setDuration(300)
        self.size_anim.setStartValue(start_size)
        self.size_anim.setEndValue(end_size)
        self.size_anim.start()

        # -------------------- Mode Progress Animation --------------------
        self.mode_anim_target = 1.0 if self.compact_mode else 0.0

        # -------------------- Fade Animation --------------------
        self.fade_anim = QVariantAnimation()
        self.fade_anim.setStartValue(0.7)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setDuration(300)
        self.fade_anim.valueChanged.connect(lambda val: setattr(self, 'mode_opacity', val))
        self.fade_anim.start()

        # -------------------- Save Adsorption Info for Snap --------------------
        self.adsorb_info = {
            'is_left_adsorbed': is_left_adsorbed,
            'is_right_adsorbed': is_right_adsorbed,
            'is_top_adsorbed': is_top_adsorbed,
            'is_bottom_adsorbed': is_bottom_adsorbed,
            'current_x': current_x,
            'current_y': current_y,
            'current_width': current_width
        }

        self.size_anim.finished.connect(self.snapAndBounce)

    def snapAndBounce(self):
        """Snap window to edge and add small bounce effect"""
        screen = QApplication.primaryScreen().availableGeometry()
        info = self.adsorb_info

        if info['is_right_adsorbed']:
            new_x = screen.right() - self.width()
            new_y = info['current_y']
        elif info['is_left_adsorbed']:
            new_x = screen.left()
            new_y = info['current_y']
        else:
            new_x = info['current_x']
            new_y = info['current_y']

        self.move(new_x, new_y)
        end_pos = self.pos()
        self.bounce_anim = QPropertyAnimation(self, b"pos")
        self.bounce_anim.setDuration(150)
        self.bounce_anim.setKeyValueAt(0, end_pos)
        self.bounce_anim.setKeyValueAt(0.5, end_pos - QPoint(0, 8))
        self.bounce_anim.setKeyValueAt(1, end_pos)
        self.bounce_anim.start()

    def updateModeAnimation(self):
        """Smooth mode progress animation"""
        self.mode_progress = self.mode_progress * 0.8 + self.mode_anim_target * 0.2
        self.update()

    @pyqtProperty(float)
    def drag_opacity(self):
        return self._drag_opacity

    @drag_opacity.setter
    def drag_opacity(self, value):
        self._drag_opacity = value
        self.setWindowOpacity(value)

    @pyqtProperty(float)
    def mode_opacity(self):
        return self._mode_opacity

    @mode_opacity.setter
    def mode_opacity(self, value):
        self._mode_opacity = value
        self.update()

    # -------------------- Display Mode --------------------
    def toggleDisplayMode(self):
        self.show_percentage = not self.show_percentage
        self.config_manager.set('show_percentage', self.show_percentage)
        self.update()

    # -------------------- Tray Icon --------------------
    def on_tray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggleVisible()

    def toggleVisible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.setToRightCenter()

    def quitApplication(self):
        self.config_manager.set('window_position', {'x': self.x(), 'y': self.y()})
        self.config_manager.set('compact_mode', self.compact_mode)
        self.config_manager.set('show_percentage', self.show_percentage)
        self.config_manager.set('auto_start', self.auto_start_manager.is_enabled())
        QApplication.quit()

    # -------------------- Network --------------------
    def updateSpeed(self):
        self.network_monitor.update_speed()
        speeds = self.network_monitor.get_speeds()
        self.download_speed = speeds['download']
        self.upload_speed = speeds['upload']

    def updateAnimation(self):
        """Smooth traffic bar animation and font size adaptation"""
        target_dl = min(self.download_speed / 512, 1.0)
        target_ul = min(self.upload_speed / 512, 1.0)
        self._download_animation = self._download_animation * 0.7 + target_dl * 0.3
        self._upload_animation = self._upload_animation * 0.7 + target_ul * 0.3

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
        return metrics.horizontalAdvance(text)

    # -------------------- Mouse Events --------------------
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
            self.config_manager.set('window_position', {'x': self.x(), 'y': self.y()})

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggleWindowMode()

    # -------------------- Painting --------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self.mode_opacity)
        rect = self.rect()

        self.ui_painter.paint_background(painter, rect)

        if self.compact_mode or self.mode_progress > 0.1:
            self.ui_painter.paint_compact_mode(painter, rect, self._download_animation, self._upload_animation)
        else:
            self.ui_painter.paint_full_mode(
                painter, rect, self.mode_progress,
                self._download_animation, self._upload_animation,
                self.show_percentage, self.download_speed, self.upload_speed,
                self.current_font_size, self.language_manager
            )

    # -------------------- Auto Snap --------------------
    def snapToEdge(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x, y, w, h = self.x(), self.y(), self.width(), self.height()
        left_distance = abs(x - screen.left())
        right_distance = abs(screen.right() - (x + w))
        top_distance = abs(y - screen.top())
        bottom_distance = abs(screen.bottom() - (y + h))
        window_center_x, window_center_y = x + w/2, y + h/2

        target_x, target_y = x, y

        if left_distance < right_distance and left_distance < 100:
            target_x = screen.left()
        elif right_distance < 100:
            target_x = screen.right() - w
        else:
            if window_center_x < screen.left():
                target_x = screen.left()
            elif window_center_x > screen.right():
                target_x = screen.right() - w

        if top_distance < 50:
            target_y = screen.top()
        elif bottom_distance < 50:
            target_y = screen.bottom() - h
        else:
            if window_center_y < screen.top():
                target_y = screen.top()
            elif window_center_y > screen.bottom():
                target_y = screen.bottom() - h

        self.snap_anim.stop()
        self.snap_anim.setStartValue(self.pos())
        self.snap_anim.setEndValue(QPoint(target_x, target_y))
        self.snap_anim.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    floater = FloaterWidget()
    sys.exit(app.exec_())
