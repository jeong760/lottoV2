# ui/widgets/venus_drum_widget.py
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("VenusDrumWidget")

import math
import random
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QSizePolicy
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QRadialGradient, QFont
from ui.widgets.lotto_ball_widget import LottoBallWidget

class VenusDrumWidget(QGroupBox):
    """
    High-resolution Venus Drum mixing chamber widget featuring an optimized radius 180 glass chamber, 
    high-speed physics simulation, and high-definition colored lotto balls.
    """
    def __init__(self, parent=None):
        super().__init__("Venus Live Drawing Chamber", parent)
        self.is_mixing = False
        self.rpm = 0
        self.extracted_balls = []
        self.ball_particles = []  # Physics simulation particles for unextracted balls
        
        # Strict Timing Rules Configuration
        self.mixing_duration_sec = 300  # 300 seconds mixing time
        self.extraction_interval_sec = 10  # 10 seconds extraction interval
        
        # Set exact minimum height to fully display the tray without extra blank space
        self.setMinimumHeight(480)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Initialize all 45 unique balls inside the optimized chamber (Radius 180)
        cx, cy, drum_radius = 200.0, 210.0, 180.0
        floor_radius = drum_radius - 35.0

        for i in range(45):
            ball_num = i + 1
            layer = i // 15  # 3 distinct depth layers
            angle_offset = math.pi * 0.70 + ((i % 15) / 14.0) * (math.pi * 0.60)
            r_jitter = floor_radius - (layer * 13.0) - random.uniform(0.0, 8.0)
            
            bx = cx + r_jitter * math.cos(angle_offset)
            by = cy + r_jitter * math.sin(angle_offset)
            
            self.ball_particles.append({
                'num': ball_num,
                'x': bx,
                'y': by,
                'vx': 0.0,
                'vy': 0.0
            })

        # Pre-calculate naturally staggered standby positions inside the chamber
        self._arrange_standby_positions(200.0)

        self.init_ui()
        _log.info("VenusDrumWidget initialized successfully with high-definition colored balls.")

    def _arrange_standby_positions(self, cx: float = 200.0):
        """Arranges all 45 balls in a natural, staggered dome-like stack nestled at the bottom of the glass sphere."""
        cy = 210.0
        
        sorted_particles = sorted(self.ball_particles, key=lambda p: p['num'])
        
        row_configs = [
            {'y_offset': 118.0, 'count': 15, 'spread': 118.0, 'stagger': 0.0},    # Bottom row (15 balls)
            {'y_offset': 92.0,  'count': 13, 'spread': 102.0, 'stagger': 5.0},    # 2nd row (13 balls)
            {'y_offset': 66.0,  'count': 10, 'spread': 78.0,  'stagger': -3.0},   # 3rd row (10 balls)
            {'y_offset': 40.0,  'count': 7,  'spread': 50.0,  'stagger': 2.0}     # Top row (7 balls)
        ]
        
        idx = 0
        for row in row_configs:
            y_pos = cy + row['y_offset']
            count = row['count']
            spread = row['spread']
            stagger = row['stagger']
            
            for c in range(count):
                if idx >= len(sorted_particles):
                    break
                p = sorted_particles[idx]
                
                if count > 1:
                    offset_x = stagger - (spread / 2.0) + c * (spread / float(count - 1))
                else:
                    offset_x = stagger
                
                p['x'] = cx + offset_x
                p['y'] = y_pos
                p['vx'] = 0.0
                p['vy'] = 0.0
                idx += 1

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 8)

        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
                color: #2c3e50;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-position: top left;
                subcontrol-origin: margin;
                left: 10px;
                padding: 2px 6px;
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 4px;
            }
        """)

    def set_mixing(self, mixing: bool, rpm: int = 0):
        self.is_mixing = mixing
        self.rpm = rpm
        if mixing:
            self.extracted_balls.clear()
            for p in self.ball_particles:
                p['vx'] = random.uniform(-14.0, 14.0)
                p['vy'] = random.uniform(-14.0, -6.0)
            _log.info(f"Venus drum mixing started at {rpm} RPM.")
        else:
            current_cx = self.width() / 2.0 if self.width() > 0 else 200.0
            self._arrange_standby_positions(current_cx)
            _log.info("Venus drum mixing stopped.")
        self.update()

    def add_extracted_ball(self, ball_num: int):
        """Adds extracted ball to tray without removing physical particles from the chamber."""
        if ball_num not in self.extracted_balls and len(self.extracted_balls) < 7:
            self.extracted_balls.append(ball_num)
            _log.debug(f"Ball #{ball_num} added to extraction tray.")
            self.update()

    def update_physics(self):
        """Updates internal ball physics scaled to the optimized radius 180 chamber boundaries."""
        cx = self.width() / 2.0 if self.width() > 0 else 200.0
        cy = 210.0
        drum_radius = 180.0
        ball_radius = 15.0
        max_allowed_dist = drum_radius - ball_radius - 4.0

        if not self.is_mixing:
            return

        speed_factor = (self.rpm / 720.0)
        for p in self.ball_particles:
            p['x'] += p['vx'] * speed_factor
            p['y'] += (p['vy'] + 0.95) * speed_factor

            p['vx'] += random.uniform(-4.5, 4.5)
            p['vy'] += random.uniform(-4.5, 4.5)
            p['vx'] = max(-21.0, min(21.0, p['vx']))
            p['vy'] = max(-21.0, min(21.0, p['vy']))

            dx = p['x'] - cx
            dy = p['y'] - cy
            dist = math.hypot(dx, dy)

            if dist > max_allowed_dist:
                angle = math.atan2(dy, dx)
                p['x'] = cx + max_allowed_dist * math.cos(angle)
                p['y'] = cy + max_allowed_dist * math.sin(angle)
                p['vx'] = -p['vx'] * 0.82
                p['vy'] = -p['vy'] * 0.82

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        painter.fillRect(self.rect(), QColor("#f4f6f9"))

        cx = width / 2.0
        cy = 210.0
        drum_radius = 180.0

        if not self.is_mixing and self.ball_particles:
            self._arrange_standby_positions(cx)

        # 1. Draw Attached Pedestal Stand & Base Structure
        stand_y = cy + drum_radius - 6
        stand_rect = QRectF(cx - 55, stand_y, 110, 26)
        
        painter.setPen(QPen(QColor("#7f8c8d"), 2))
        painter.setBrush(QBrush(QColor("#bdc3c7")))
        painter.drawRoundedRect(stand_rect, 4, 4)

        # 2. Draw Optimized Uncut Glass Chamber (Radius 180 Sphere)
        drum_rect = QRectF(cx - drum_radius, cy - drum_radius, drum_radius * 2, drum_radius * 2)

        drum_gradient = QRadialGradient(cx - 35, cy - 35, drum_radius * 1.3)
        drum_gradient.setColorAt(0.0, QColor("#ffffff"))
        drum_gradient.setColorAt(0.7, QColor("#e8f4f8"))
        drum_gradient.setColorAt(1.0, QColor("#b2bec3"))

        painter.setPen(QPen(QColor("#576574"), 4))
        painter.setBrush(QBrush(drum_gradient))
        painter.drawEllipse(drum_rect)

        # Inner chamber shadow effect
        painter.setPen(QPen(QColor("#dcdde1"), 2))
        painter.setBrush(QBrush(QColor("#f8f9fa")))
        painter.drawEllipse(QRectF(cx - (drum_radius - 10), cy - (drum_radius - 10), (drum_radius - 10) * 2, (drum_radius - 10) * 2))

        # 3. Draw all 45 persistent balls inside the chamber using high-definition LottoBallWidget renderer
        for p in self.ball_particles:
            LottoBallWidget.draw_ball(painter, p['x'], p['y'], p['num'], radius=15.0, show_label=True)

        # 4. Draw Extraction Tray at the bottom
        tray_y = stand_y + 26
        tray_width = 390
        tray_height = 52
        tray_rect = QRectF(cx - (tray_width / 2.0), tray_y, tray_width, tray_height)

        painter.setPen(QPen(QColor("#7f8c8d"), 2))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRoundedRect(tray_rect, 8, 8)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#f1f2f6")))
        painter.drawRoundedRect(QRectF(cx - (tray_width / 2.0) + 4, tray_y + 4, tray_width - 8, tray_height - 8), 6, 6)

        max_slots = 7
        spacing = 48.0
        start_x = cx - ((max_slots * spacing) / 2.0) + (spacing / 2.0)
        slot_radius = 16.0

        # Draw empty slot guidelines in the tray
        for i in range(max_slots):
            sx = start_x + (i * spacing)
            sy = tray_y + (tray_height / 2.0) - 5
            is_bonus_slot = (i == 6)

            slot_pen = QPen(QColor("#e74c3c" if is_bonus_slot else "#bdc3c7"), 1.5, Qt.DashLine if is_bonus_slot else Qt.SolidLine)
            painter.setPen(slot_pen)
            painter.setBrush(QBrush(QColor("#fafbfc")))
            painter.drawEllipse(QRectF(sx - slot_radius, sy - slot_radius, slot_radius * 2, slot_radius * 2))

            if is_bonus_slot:
                painter.setPen(QPen(QColor("#e74c3c")))
                font = QFont("Segoe UI", 5, QFont.Bold)
                painter.setFont(font)
                painter.drawText(QRectF(sx - 18, tray_y + tray_height - 17, 36, 14), Qt.AlignCenter, "BONUS")

        # Draw actual extracted balls over the slots using high-definition LottoBallWidget renderer
        for i, num in enumerate(self.extracted_balls):
            if i >= max_slots:
                break
            bx = start_x + (i * spacing)
            by = tray_y + (tray_height / 2.0) - 5
            is_bonus = (i == 6)
            
            LottoBallWidget.draw_ball(painter, bx, by, num, radius=15.0, is_bonus=is_bonus, show_label=True)