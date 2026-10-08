# -*- coding: utf-8 -*-
# ui/widgets/algorithm_radar_widget.py
import sys
import os
import logging
import math

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("AlgorithmRadarWidget")

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF


class AlgorithmRadarWidget(QWidget):
    """
    Algorithm Performance Radar Chart Widget.
    Evaluates and plots multi-dimensional metrics (e.g., Uniformity, Periodicity, 
    Sector Balance, Co-occurrence Weight, and Entropy) on a 5-axis radar chart.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set compact minimum size to optimize horizontal layout space
        self.setMinimumSize(110, 110)
        # Default metric scores (0.0 to 100.0)
        self.metrics = {
            "Uniformity": 78.5,
            "Periodicity": 65.0,
            "Sector Balance": 82.0,
            "Pair Affinity": 70.5,
            "Entropy Rate": 88.0
        }

    def update_radar_metrics(self, new_metrics: dict):
        """
        Updates the multi-dimensional metrics dictionary and triggers repaint.
        :param new_metrics: Dict containing key-value performance scores.
        """
        if new_metrics and isinstance(new_metrics, dict):
            self.metrics.update(new_metrics)
            self.update()

    def update_metrics(self, new_metrics: dict):
        """Compatibility alias for update_radar_metrics."""
        self.update_radar_metrics(new_metrics)

    def set_data(self, new_metrics: dict):
        """Compatibility alias for update_radar_metrics."""
        self.update_radar_metrics(new_metrics)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # [Widget Container Box] Card background and border (White background + Gray border)
        painter.setPen(QPen(QColor("#dcdde1"), 1))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRoundedRect(2, 2, width - 4, height - 4, 6, 6)

        # Title (Optimized top margin and font size)
        painter.setPen(QColor("#2c3e50"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(10, 16, "Multi-Dimensional Algorithm Radar Profile")

        cx = width / 2.0
        # Center point vertical balance adjustment
        cy = (height / 2.0) + 10
        # Radar chart radius scale configuration
        radius = min(width * 0.18, height * 0.22)

        categories = list(self.metrics.keys())
        num_vars = len(categories)
        if num_vars == 0:
            return

        # Draw concentric web polygons (4 grid levels)
        levels = 4
        for level in range(1, levels + 1):
            r = radius * (level / levels)
            painter.setPen(QPen(QColor("#dcdde1"), 1, Qt.SolidLine))
            
            polygon_points = []
            for i in range(num_vars):
                angle = (math.pi * 2 / num_vars) * i - (math.pi / 2)
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                polygon_points.append(QPointF(x, y))
            
            painter.drawPolygon(QPolygonF(polygon_points))

        # Draw axis spokes from center
        painter.setPen(QPen(QColor("#bdc3c7"), 1, Qt.DashLine))
        for i in range(num_vars):
            angle = (math.pi * 2 / num_vars) * i - (math.pi / 2)
            x_end = cx + radius * math.cos(angle)
            y_end = cy + radius * math.sin(angle)
            painter.drawLine(QPointF(cx, cy), QPointF(x_end, y_end))

            # Draw Category Labels (Simplified and optimized with center alignment)
            cat_name = categories[i]
            score_val = self.metrics.get(cat_name, 0.0)
            label_radius = radius * 1.35
            lx = cx + label_radius * math.cos(angle)
            ly = cy + label_radius * math.sin(angle)

            painter.setPen(QColor("#34495e"))
            painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
            
            box_width = 54
            box_height = 18

            # Apply center alignment and box centering
            align = Qt.AlignCenter
            lx -= box_width / 2.0
            ly -= box_height / 2.0

            # Constrain coordinates within widget boundaries to avoid clipping
            lx = max(4, min(width - box_width - 4, lx))
            ly = max(16, min(height - box_height - 4, ly))

            painter.drawText(int(lx), int(ly), box_width, box_height, align, f"{cat_name} ({score_val:.0f})")

        # Map metric scores (0 - 100) to radar polygon points
        data_polygon_points = []
        for i, cat in enumerate(categories):
            score = max(0.0, min(100.0, self.metrics.get(cat, 0.0)))
            factor = score / 100.0
            angle = (math.pi * 2 / num_vars) * i - (math.pi / 2)
            
            x = cx + radius * factor * math.cos(angle)
            y = cy + radius * factor * math.sin(angle)
            data_polygon_points.append(QPointF(x, y))

        # Fill data polygon area with semi-transparent cyan/blue gradient
        fill_brush = QBrush(QColor(41, 128, 185, 60))
        painter.setBrush(fill_brush)
        painter.setPen(QPen(QColor("#2980b9"), 2, Qt.SolidLine))
        painter.drawPolygon(QPolygonF(data_polygon_points))

        # Draw vertices nodes on the polygon
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#2980b9"), 2))
        for pt in data_polygon_points:
            painter.drawEllipse(pt, 2, 2)