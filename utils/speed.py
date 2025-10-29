
import threading
import time
from typing import List, Tuple, Optional

class SpeedBuffer:
    def __init__(self):
        self.lock = threading.Lock()
        self.samples: List[Tuple[float, float]] = []  # (t, mph)
        self.t0 = time.time()

    def add(self, mph: float):
        with self.lock:
            self.samples.append((time.time() - self.t0, float(mph)))
            if len(self.samples) > 6000:
                self.samples = self.samples[-6000:]

    def get(self) -> List[Tuple[float, float]]:
        with self.lock:
            return list(self.samples)

class OBDSpeedThread(threading.Thread):
    def __init__(self, buf: SpeedBuffer, period: float = 0.1):
        super().__init__(daemon=True)
        self.buf = buf
        self.period = period
        self._stop = threading.Event()
        self._connected = False
        self._err = None

    def run(self):
        try:
            import obd
            try:
                connection = obd.OBD()
                self._connected = connection.is_connected()
            except Exception as e:
                connection = None
                self._connected = False
                self._err = str(e)

            while not self._stop.is_set():
                if connection and connection.is_connected():
                    rsp = connection.query(obd.commands.SPEED)
                    mph = rsp.value.magnitude if (rsp and not rsp.is_null()) else 0.0
                else:
                    mph = 0.0
                self.buf.add(mph)
                time.sleep(self.period)
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass
        except Exception as e:
            self._err = str(e)

    def stop(self):
        self._stop.set()

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def error(self) -> Optional[str]:
        return self._err

class GPSSpeedThread(threading.Thread):
    def __init__(self, buf: SpeedBuffer, period: float = 1.0):
        super().__init__(daemon=True)
        self.buf = buf
        self.period = period
        self._stop = threading.Event()
        self._ok = False
        self._err = None

    def run(self):
        try:
            from gpsdclient import GPSDClient
            with GPSDClient(host="127.0.0.1", port=2947) as client:
                self._ok = True
                for result in client.dict_stream(filter=["TPV"]):
                    if self._stop.is_set():
                        break
                    try:
                        spd_ms = result.get("speed", 0.0) or 0.0
                        mph = float(spd_ms) * 2.23693629
                        self.buf.add(mph)
                    except Exception:
                        pass
                    time.sleep(self.period)
        except Exception as e:
            self._err = str(e)
            self._ok = False

    def stop(self):
        self._stop.set()

    @property
    def ok(self) -> bool:
        return self._ok

    @property
    def error(self) -> Optional[str]:
        return self._err
