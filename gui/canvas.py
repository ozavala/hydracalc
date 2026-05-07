import sys
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget, QApplication, QMainWindow, QHBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen, QTransform
from PySide6.QtCore import Qt, QPointF, Signal

@dataclass
class NodeData:
    id: int
    pressure: float
    elevation: float
    notes: str

class NetworkCanvas(QWidget):
    nodeSelected = Signal(NodeData)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        # Estado de la vista
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self.last_mouse_pos = QPointF()
        self.grid_size = 30
        self.selected_node_idx = None

        # --- ESTRUCTURA CORREGIDA ---
        # Ahora los nodos contienen su posición y su data
        self.nodes = [
            {"pos": QPointF(100, 100), "data": NodeData(1, 2.5, 10.0, "Tanque Principal")},
            {"pos": QPointF(400, 200), "data": NodeData(2, 1.8, 5.0, "Punto de Demanda")}
        ]
        # Las tuberías ahora referencian los diccionarios de arriba
        self.pipes = [(0, 1)] 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            painter.fillRect(self.rect(), QColor("white"))

            transform = QTransform()
            transform.translate(self.pan_offset.x(), self.pan_offset.y())
            transform.scale(self.zoom_factor, self.zoom_factor)
            painter.setTransform(transform)

            self.draw_grid(painter)
            self.draw_network(painter)
        finally:
            # Esto evita el error de "active painter" si algo falla
            painter.end()

    def draw_grid(self, painter):
        pen = QPen(QColor(240, 240, 240), 1)
        painter.setPen(pen)
        r = 3000
        for x in range(-r, r, self.grid_size):
            painter.drawLine(x, -r, x, r)
        for y in range(-r, r, self.grid_size):
            painter.drawLine(-r, y, r, y)

    def draw_network(self, painter):
        # 1. Dibujar Tuberías (Pipes)
        pen_pipe = QPen(QColor("#2c3e50"), 3)
        painter.setPen(pen_pipe)
        for start_idx, end_idx in self.pipes:
            p1 = self.nodes[start_idx]["pos"]
            p2 = self.nodes[end_idx]["pos"]
            painter.drawLine(p1, p2)

        # 2. Dibujar Nodos
        for i, node_dict in enumerate(self.nodes):
            # Si está seleccionado, pintar de otro color
            color = "#e74c3c" if i == self.selected_node_idx else "#3498db"
            painter.setBrush(QColor(color))
            painter.setPen(QPen(QColor("black"), 1))
            painter.drawEllipse(node_dict["pos"], 8, 8)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Hit testing: ¿Qué nodo tocamos?
            transform = QTransform()
            transform.translate(self.pan_offset.x(), self.pan_offset.y())
            transform.scale(self.zoom_factor, self.zoom_factor)
            
            # Invertir la transformación para saber dónde hicimos clic en el "mundo real"
            world_pos = transform.inverted()[0].map(event.position())
            
            self.selected_node_idx = None
            for i, node in enumerate(self.nodes):
                dist = (node["pos"] - world_pos).manhattanLength()
                if dist < 15:
                    self.selected_node_idx = i
                    self.nodeSelected.emit(node["data"])
                    break
            self.update()
        
        elif event.button() == Qt.MiddleButton:
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MiddleButton:
            delta = event.position() - self.last_mouse_pos
            self.pan_offset += delta
            self.last_mouse_pos = event.position()
            self.update()

    def wheelEvent(self, event):
        adj = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.zoom_factor *= adj
        self.update()
