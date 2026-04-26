import logging

logger = logging.getLogger(__name__)


def safe_dispatch(task, *args, **kwargs):
    try:
        task.delay(*args, **kwargs)
    except Exception as exc:  # pragma: no cover - defensive production fallback
        # If broker is unavailable, we do not want critical user flows like registration
        # or joining a game to fail. We execute synchronously as a graceful fallback.
        logger.warning('Async dispatch failed for %s, running synchronously. Error: %s', task.name, exc)
        task.apply(args=args, kwargs=kwargs)
