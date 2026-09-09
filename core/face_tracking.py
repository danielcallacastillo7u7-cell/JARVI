"""Local face landmarks and observable gestures. No recording or network calls."""
from __future__ import annotations
import json
import platform
import threading
import time
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

_tracker = None

def gesture_labels(scores):
    avg = lambda a,b: (scores.get(a,0) + scores.get(b,0)) / 2
    labels=[]
    if avg('mouthSmileLeft','mouthSmileRight') > .40: labels.append('Sonrisa')
    if scores.get('jawOpen',0) > .45: labels.append('Boca abierta')
    if max(scores.get('browInnerUp',0),avg('browOuterUpLeft','browOuterUpRight')) > .45:
        labels.append('Cejas levantadas')
    if avg('browDownLeft','browDownRight') > .45: labels.append('Ceño fruncido')
    if avg('eyeBlinkLeft','eyeBlinkRight') > .65: labels.append('Ojos cerrados')
    return labels or ['Sin gesto marcado']

def get_tracker(model_path=None):
    global _tracker
    if _tracker is None and model_path is not None:
        _tracker=FaceTracker(model_path)
    return _tracker

def camera_frame():
    """Reuse the active camera for explicit vision requests; never open it twice."""
    tracker=get_tracker()
    if tracker is None or not tracker.running:
        return None
    if tracker._stop.is_set():
        raise RuntimeError('La cámara se está cerrando. Inténtalo de nuevo en un momento.')
    with tracker._lock:
        if tracker._frame is not None and time.monotonic()-tracker._frame_time < 2:
            return tracker._frame.copy()
    raise RuntimeError('La cámara facial aún no tiene una imagen disponible. Inténtalo de nuevo.')

def describe_expression():
    tracker=get_tracker()
    if tracker is None:
        return 'El seguimiento facial no está iniciado.'
    with tracker._lock:
        data=tracker._latest.copy()
    if not tracker.running or time.monotonic()-data.get('time',0)>2:
        return 'No hay una lectura facial actual. Activa la malla con F8.'
    if not data.get('points'):
        return 'No se detecta un rostro. No deduzcas expresiones ni emociones.'
    return ('Gestos visibles aproximados: '+', '.join(data['labels'])+
            '. Estos gestos no prueban emociones, intenciones ni estados de salud.')

class FaceTracker(QObject):
    updated=pyqtSignal(object)

    def __init__(self,model_path):
        super().__init__()
        self.model_path=Path(model_path)
        self._lock=threading.Lock()
        self._stop=threading.Event()
        self._thread=None
        self._latest={}
        self._frame=None
        self._frame_time=0

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running: return
        self._stop.clear()
        self._thread=threading.Thread(target=self._run,daemon=True,name='face-mesh')
        self._thread.start()

    def stop(self):
        self._stop.set()
        with self._lock:
            self._latest={}
            self._frame=None
        self.updated.emit({'status':'Cámara pausada','points':[],'labels':[],'active':False})

    def _publish(self,**data):
        if self._stop.is_set(): return
        data['time']=time.monotonic()
        with self._lock: self._latest=data
        self.updated.emit(data)

    def _run(self):
        cap=None
        failure=None
        try:
            self._publish(status='Preparando cámara…',points=[],labels=[],active=True)
            import cv2
            import mediapipe as mp
            if not self.model_path.is_file():
                raise RuntimeError('Falta el modelo facial local')
            index=0
            config=self.model_path.parent.parent/'config'/'api_keys.json'
            try: index=int(json.loads(config.read_text(encoding='utf-8')).get('camera_index',0))
            except (OSError,ValueError,TypeError): pass
            options=mp.tasks.vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(self.model_path)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_faces=1,output_face_blendshapes=True)
            edges=[(c.start,c.end) for c in
                   mp.tasks.vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION]
            with mp.tasks.vision.FaceLandmarker.create_from_options(options) as detector:
                if self._stop.is_set(): return
                backend=cv2.CAP_DSHOW if platform.system()=='Windows' else cv2.CAP_ANY
                cap=cv2.VideoCapture(index,backend)
                if not cap.isOpened(): raise RuntimeError('Cámara no disponible o en uso')
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
                cap.set(cv2.CAP_PROP_FPS,15)
                previous={}
                timestamp=0
                failures=0
                while not self._stop.is_set():
                    started=time.monotonic()
                    ok,frame=cap.read()
                    if self._stop.is_set(): break
                    if not ok:
                        failures+=1
                        if failures>=12: raise RuntimeError('No se reciben imágenes de la cámara')
                        self._publish(status='Esperando cámara…',points=[],labels=[],active=True)
                        self._stop.wait(.1)
                        continue
                    failures=0
                    with self._lock:
                        self._frame=frame.copy()
                        self._frame_time=started
                    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                    image=mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
                    timestamp=max(timestamp+1,int(time.monotonic()*1000))
                    result=detector.detect_for_video(image,timestamp)
                    if result.face_landmarks:
                        raw={c.category_name:c.score for c in result.face_blendshapes[0]}
                        smooth={k:.55*v+.45*previous.get(k,v) for k,v in raw.items()}
                        previous=smooth
                        points=[(1-p.x,p.y,p.z) for p in result.face_landmarks[0]]
                        self._publish(status='Seguimiento local activo',active=True,
                                      points=points,edges=edges,labels=gesture_labels(smooth),
                                      aspect=frame.shape[1]/frame.shape[0])
                    else:
                        previous={}
                        self._publish(status='No se detecta un rostro',active=True,
                                      points=[],edges=[],labels=[])
                    self._stop.wait(max(0,.083-(time.monotonic()-started)))
        except Exception as exc:
            failure=('Falta instalar MediaPipe' if isinstance(exc,ImportError)
                     else str(exc)[:150])
        finally:
            if cap is not None: cap.release()
            with self._lock:
                self._frame=None
                self._latest={}
            self.updated.emit({'status':failure or 'Cámara pausada',
                               'points':[],'labels':[],'active':False})
