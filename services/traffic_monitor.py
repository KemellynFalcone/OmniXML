"""Aggregate process counters in RAM. No events, identifiers or request bodies."""
import os
import threading
import time
from flask import g, request

_lock = threading.Lock()
_started = time.monotonic()
_counts = {'requests':0, 'active':0, 'success':0, 'rejected':0, 'errors':0, 'bytes_in':0, 'bytes_out':0, 'duration_ms':0, 'fiscal':0, 'access':0, 'pages':0}


def install(app):
    @app.before_request
    def begin():
        if request.path.startswith('/static/') or request.path == '/api/admin/traffic':
            return
        g.traffic_start = time.monotonic()
        with _lock:
            _counts['requests'] += 1
            _counts['active'] += 1
            _counts['bytes_in'] += max(0, request.content_length or 0)
            category = 'fiscal' if request.path == '/api/sefaz/recover' else 'access' if request.path.startswith('/api/access/') else 'pages'
            _counts[category] += 1

    @app.after_request
    def finish(response):
        if hasattr(g, 'traffic_start'):
            with _lock:
                _counts['active'] -= 1
                category = 'success' if response.status_code < 400 else 'rejected' if response.status_code < 500 else 'errors'
                _counts[category] += 1
                _counts['bytes_out'] += max(0, response.content_length or 0)
                _counts['duration_ms'] += round((time.monotonic()-g.traffic_start)*1000)
            del g.traffic_start
        return response

    @app.teardown_request
    def interrupted(error):
        if hasattr(g, 'traffic_start'):
            with _lock:
                _counts['active'] -= 1
                _counts['errors'] += 1
                _counts['duration_ms'] += round((time.monotonic()-g.traffic_start)*1000)
            del g.traffic_start


def snapshot():
    with _lock:
        result = dict(_counts)
    completed = result['success']+result['rejected']+result['errors']
    result['average_ms'] = round(result.pop('duration_ms')/completed) if completed else 0
    result['uptime_seconds'] = int(time.monotonic()-_started)
    result['worker'] = os.getpid()
    return result
