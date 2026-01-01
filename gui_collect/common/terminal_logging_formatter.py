import re
import logging


tag_pattern = re.compile(r"(<.*?>[\s\S]*?<\/.*?>)")


class TerminalLoggingFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(fmt="%(message)s", datefmt="%H:%M:%S")
        self.tag_by_levelname = [
            ('<ERROR>', '</ERROR>', logging.getLevelName(logging.ERROR)),
            ('<WARNING>', '</WARNING>', logging.getLevelName(logging.WARNING))
        ]

    def format(self, record: logging.LogRecord):
        record.message = record.getMessage()
        msg = self.formatMessage(record)

        if getattr(record, 'TIMESTAMP', True) is True:
            record.asctime = self.formatTime(record, self.datefmt)
            msg = f'<TIMESTAMP>[{record.asctime}]</TIMESTAMP> {msg}'
        else:
            msg = f"{' ' * 10} {msg}"

        # from super
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if msg[-1:] != "\n":
                msg = msg + "\n"
            msg = msg + record.exc_text
        if record.stack_info:
            if msg[-1:] != "\n":
                msg = msg + "\n"
            msg = msg + self.formatStack(record.stack_info)

        # Wrap text with a tag based on logging record level unless the text is already wrapped by a tag
        parts = tag_pattern.split(msg)
        for tag_start, tag_end, levelname in self.tag_by_levelname:
            if record.levelname == levelname:
                msg = ''.join([
                    s if s.startswith('<')
                    else f"{tag_start}{s}{tag_end}"
                    for s in parts if len(s) > 0
                ])
                break

        return msg

