# ============================================================================
# CRITICAL FIXES: Request Cancellation & Enhanced Cache
# ============================================================================

class RequestToken:
    """Token system for cancellable requests - FIX FOR RACE CONDITIONS"""
    def __init__(self):
        self._cancelled = False
        self._lock = threading.Lock()
    
    def cancel(self):
        with self._lock:
            self._cancelled = True
    
    def is_cancelled(self):
        with self._lock:
            return self._cancelled
    
    def check_cancelled(self):
        if self.is_cancelled():
            raise RequestCancelledException("Request was cancelled")

class RequestCancelledException(Exception):
    """Exception raised when request is cancelled"""
    pass

class CancellableRequestManager:
    """Manages cancellable async requests to prevent race conditions"""
    def __init__(self):
        self._active_requests = {}
        self._lock = threading.Lock()
    
    def start_request(self, request_id):
        with self._lock:
            if request_id in self._active_requests:
                self._active_requests[request_id].cancel()
            token = RequestToken()
            self._active_requests[request_id] = token
            return token
    
    def finish_request(self, request_id):
        with self._lock:
            if request_id in self._active_requests:
                del self._active_requests[request_id]
    
    def cancel_all(self):
        with self._lock:
            for token in self._active_requests.values():
                token.cancel()
            self._active_requests.clear()

