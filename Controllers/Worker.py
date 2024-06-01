import sys
import traceback
from threading import Event

import numpy as np
from PySide6.QtCore import QObject, Signal, QRunnable, QMutex, QThreadPool, Slot


class WorkerSignals(QObject):
    processed = Signal(object)
    terminated = Signal()


class Worker(QRunnable):
    def __init__(self):
        super(Worker, self).__init__()
        self.signals = WorkerSignals()
        self.terminate = False
        self.new_data_arrived = Event()
        self.mutex = QMutex()
        self.f = None
        self.params = None
        self.split_dimensions = True
        self.threadpool = QThreadPool()

    def run(self):
        print("Worker started")
        while not self.terminate:
            try:
                self.new_data_arrived.wait(timeout=1)
            except:
                pass

            if self.new_data_arrived.is_set():
                self.mutex.lock()
                self.new_data_arrived.clear()
                f = self.f
                params = self.params
                self.mutex.unlock()

                try:
                    if len(params[0].shape) == 2 or not self.split_dimensions:
                        output = f(*params)
                    elif len(params[0].shape) == 3:
                        finished_events = []
                        output = []

                        for i in range(params[0].shape[2]):
                            output.append(None)
                            e = Event()
                            finished_events.append(e)
                            params_ = (params[0][:, :, i], *(params[1:]))
                            temp_worker = TemporaryWorker(f, params_, output, i, e)
                            self.threadpool.start(temp_worker)

                        for e in finished_events:
                            e.wait()

                        output = np.stack(output, axis=2)
                    self.signals.processed.emit(np.array(output))
                except Exception:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
        print("Worker stopped")

    @Slot(object, object)
    def process(self, f, parameters, split_dimensions=True):
        self.mutex.lock()
        self.f = f
        self.params = parameters
        self.split_dimensions = split_dimensions
        self.new_data_arrived.set()
        self.mutex.unlock()


class TemporaryWorker(QRunnable):
    def __init__(self, f, params, output, idx, finished_event):
        super(TemporaryWorker, self).__init__()
        self.f = f
        self.params = params
        self.output = output
        self.idx = idx
        self.finished_event = finished_event

    @Slot()
    def run(self):
        self.output[self.idx] = self.f(*self.params)
        self.finished_event.set()
