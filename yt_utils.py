import logging
import os

from typing import Union
from subprocess import CompletedProcess, CalledProcessError
from logging.handlers import TimedRotatingFileHandler

LOGGER = logging.getLogger("YT-Cache Log")
BASE_SHARE = "/data/share"
BASE_CMD = ["youtube-dl", "-i", "-f", "mp4", "-o"]
YTDL_FMT = "{0}/%(title)s.%(ext)s"
API_KEY = os.getenv("YT_API_KEY")
BASE_URL = "https://youtube.googleapis.com/youtube/v3/{0}"


def log_result(result: Union[CompletedProcess, CalledProcessError]) -> None:
    """
    Parses how youtube-dl likes to format their STDOUT/STDERR thanks to ANSI codes
    Outputs both outputs to logging
    """

    def parse_output(out: bytes) -> str:
        parsed = out.decode("utf-8").rstrip("\n").replace("\r", "\n").split("\n")
        return "\n".join([x for x in parsed if x != ""])

    LOGGER.info("STDOUT ~>\n" + parse_output(result.stdout))
    LOGGER.error("STDERR ~>\n" + parse_output(result.stderr))


def config_logger(log_file: str) -> logging.Logger:
    LOGGER.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(
        filename=os.path.join(BASE_SHARE, log_file), when="W1"
    )
    handler.setFormatter(
        logging.Formatter("%(levelname)-5s :: [%(asctime)s]  %(message)s")
    )
    LOGGER.addHandler(handler)
    return LOGGER
