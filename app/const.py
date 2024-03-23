import os

# Files & Directories
CONFIG_DIR = os.path.join("/", "config")

## Directory for rss feeds generated by the program.

OUTPUT_DIR = os.path.join("/", "data")

## Directory for archive and pickle files that should be persistent between
## executions.
PERSISTENT_DIR = os.path.join("/", "persistent")


# Configuration defaults.
DEFAULT_PODCAST_IMAGE_URL = "https://raw.githubusercontent.com/thorbjoernl/nrk-podcast-rss/main/img/default_podcast.png"
DEFAULT_PODCAST_TITLE = "Untitled Podcast"
DEFAULT_PODCAST_DESC = ""
DEFAULT_PODCAST_EXPLICIT = False
DEFAULT_PODCAST_EPISODE_COUNT = 10

WEEKDAY_PREFIXES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]