import time
from flask import Response, stream_with_context, jsonify
from . import main_bp
from app.utils.shutdown_monitor import on_connect, on_disconnect

@main_bp.route('/events')
def sse_events():
    """Server-Sent Events stream to detect tab presence.
    Keeps a connection open while a tab is active. When closed, we decrement
    and schedule a shutdown if no tabs remain.
    Public endpoint to track presence even before login.
    """
    def event_stream():
        on_connect()
        try:
            # Send a ping every 10 seconds to keep connection alive
            while True:
                yield 'data: ping\n\n'
                time.sleep(10)
        finally:
            on_disconnect()
    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    }
    return Response(stream_with_context(event_stream()), headers=headers)


@main_bp.route('/events/bye', methods=['POST'])
def sse_bye():
    """Explicit disconnect for beforeunload/beacon."""
    on_disconnect()
    return jsonify({'ok': True})
