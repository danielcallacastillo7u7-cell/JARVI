"""Compact cyan wireframe view embedded in the JARVIS HUD."""
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from core.face_tracking import get_tracker

class MeshCanvas(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.points=[]
        self.edges=[]
        self.aspect=4/3
        self.setMinimumHeight(140)

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(),QColor('#00080d'))
        w,h=self.width(),self.height()
        p.setPen(QPen(QColor('#087081'),2))
        for x,y,dx,dy in [(6,6,1,1),(w-6,6,-1,1),(6,h-6,1,-1),(w-6,h-6,-1,-1)]:
            p.drawLine(QPointF(x,y),QPointF(x+dx*18,y))
            p.drawLine(QPointF(x,y),QPointF(x,y+dy*18))
        if self.points:
            xs=[v[0] for v in self.points]; ys=[v[1] for v in self.points]
            left,right,top,bottom=min(xs),max(xs),min(ys),max(ys)
            # Restore camera aspect (640:480) when drawing normalized points.
            aspect=self.aspect
            scale=min((w-38)/(max(.01,right-left)*aspect),(h-28)/max(.01,bottom-top))
            pts=[QPointF(w/2+(x-(left+right)/2)*scale*aspect,
                         h/2+(y-(top+bottom)/2)*scale) for x,y,z in self.points]
            glow=QRadialGradient(QPointF(w/2,h/2),w*.55)
            glow.setColorAt(0,QColor(0,160,180,35)); glow.setColorAt(1,QColor(0,20,30,0))
            p.fillRect(self.rect(),glow)
            path=QPainterPath()
            for a,b in self.edges:
                if a<len(pts) and b<len(pts):
                    path.moveTo(pts[a]);path.lineTo(pts[b])
            p.setPen(QPen(QColor(0,225,245,28),3));p.drawPath(path)
            p.setPen(QPen(QColor(35,225,245,150),.65));p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#b1ffff'))
            for i in (1,4,33,133,362,263,61,291,10,152):
                if i<len(pts):p.drawEllipse(pts[i],1.3,1.3)
        else:
            p.setPen(QColor('#488794'))
            p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'Sin lectura facial')
        p.end()

class FaceMeshPanel(QWidget):
    def __init__(self,model_path,parent=None):
        super().__init__(parent)
        self.setObjectName('FaceMeshPanel')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        self.setStyleSheet('QWidget#FaceMeshPanel {background:#00080d;border:1px solid #087081;border-radius:8px;} QLabel {color:#73eaf4;background:transparent;border:none;font-size:11px;} QPushButton {color:#73eaf4;background:#00232b;border:1px solid #087081;border-radius:4px;padding:4px;font-size:10px;}')
        layout=QVBoxLayout(self);layout.setContentsMargins(9,8,9,8);layout.setSpacing(5)
        head=QHBoxLayout();head.addWidget(QLabel('MALLA FACIAL'));head.addStretch()
        self.button=QPushButton('ACTIVAR · F8');head.addWidget(self.button)
        layout.addLayout(head)
        self.canvas=MeshCanvas(self);layout.addWidget(self.canvas,1)
        self.gestures=QLabel('');self.gestures.setWordWrap(True);layout.addWidget(self.gestures)
        self.status=QLabel('Cámara pausada');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.tracker=get_tracker(model_path)
        self.tracker.updated.connect(self._update)
        self.button.clicked.connect(self.toggle)

    def activate(self): self.tracker.start()

    def deactivate(self): self.tracker.stop()

    def toggle(self):
        if self.tracker.running:self.deactivate()
        else:self.activate()

    def _update(self,data):
        self.canvas.points=data.get('points',[])
        self.canvas.edges=data.get('edges',[])
        self.canvas.aspect=data.get('aspect',4/3)
        self.gestures.setText(' · '.join(data.get('labels',[])))
        self.status.setText(data.get('status',''))
        self.button.setText('PAUSAR · F8' if data.get('active') else 'ACTIVAR · F8')
        self.canvas.update()
