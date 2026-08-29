class TedApiError(RuntimeError):
    """Base exception for a failed TED API request."""


class TedRateLimitError(TedApiError):
    """TED rejected a request because its rate limit was reached."""


class TedResponseError(TedApiError):
    """TED returned an unexpected response payload."""


class TedSearchTimedOutError(TedApiError):
    """TED processed a search request only partially."""
