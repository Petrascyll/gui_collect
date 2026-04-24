import logging

from collections.abc import Callable

from gui_collect.common.terminal_logging_formatter import TerminalLoggingFormatter


def get_terminal_logging_handler(_emit: Callable[[str], None]):
    formatter = TerminalLoggingFormatter()

    class TerminalLoggingHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            _emit(msg)

    handler = TerminalLoggingHandler()
    handler.setFormatter(formatter)
    return handler
