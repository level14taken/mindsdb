COMPANY_ID = None
import os
from re import S
from threading import Thread

from mindsdb.utilities.config import STOP_THREADS_EVENT
import mindsdb.interfaces.storage.db as db


class Integration:
    def __init__(self, config, name):
        self.config = config
        self.name = name
        self.mindsdb_database = config['api']['mysql']['database']

    def setup(self):
        raise NotImplementedError

    def _query(self, query, fetch=False):
        raise NotImplementedError

    def register_predictors(self, model_data_arr):
        raise NotImplementedError

    def unregister_predictor(self, name):
        raise NotImplementedError


class StreamIntegration(Integration):
    def __init__(self, config, name):
        Integration.__init__(self, config, name)
        self._streams = []
    
    def setup(self):
        Thread(target=StreamIntegration._loop, args=(self, )).start()

    def _loop(self):
        while not STOP_THREADS_EVENT.wait(1.0):
            stream_db_recs = db.session.query(db.Stream).filter_by(company_id=COMPANY_ID, integration=self.name).all()

            # Stop streams that weren't found in DB
            indices_to_delete = []
            for i, s in enumerate(self._streams):
                if s.name not in map(lambda x: x.name, stream_db_recs):
                    indices_to_delete.append(i)
                    self._streams[i].stop_event.set()
                    self._streams[i].thread.join()
            self._streams = [s for i, s in enumerate(self._streams) if i not in indices_to_delete]

            # Start new streams found in DB
            for s in stream_db_recs:
                if s.name not in map(lambda x: x.name, self._streams):
                    self._streams.append(self._make_stream(s))

        for s in self._streams:
            print('1s', s)
            s.stop_event.set()
            print('2s', s)
            s.thread.join()
            print('3s', s)

    def _make_stream(self, s):
        raise NotImplementedError

    def _query(self, query, fetch=False):
        raise NotImplementedError

    def register_predictors(self, model_data_arr):
        raise NotImplementedError

    def unregister_predictor(self, name):
        raise NotImplementedError
