import os
import logging
import configparser
import time
import yt_dlp
import datetime
import pytz
import pickle
import threading
import urllib.request
import json
from podgen import Podcast, Episode, Media

CONFIG_DIR = os.path.join("/", "config")

config = configparser.ConfigParser()
config.read(os.path.join(CONFIG_DIR, "config.ini"))

# Directory for rss feeds generated by the program.
OUTPUT_DIR = os.path.join("/", "data")

# Directory for archive and pickle files that should be persistent between
# executions.
PERSISTENT_DIR = os.path.join("/", "persistent")


def update_podcast(item: dict[str, str]):
    url = item["url"]
    title = item["name"]
    desc = item["desc"]

    # Skip podcast update based on filter settings.
    if "weekdays" in item.keys():
        if not (datetime.datetime.today().weekday() in item["weekdays"]):
            logging.info(f"Skipping {title} due to weekday filtering.")
            return
    if "hours" in item.keys():
        if not (datetime.datetime.now().hour in item["hours"]):
            logging.info(f"Skipping {title} due to hour filtering.")
            return

    # File paths for generated files.
    archive_file = os.path.join(PERSISTENT_DIR, f"{item['fname']}.txt")
    pickle_file = os.path.join(PERSISTENT_DIR, f"{item['fname']}.pickle")
    rss_file = os.path.join(OUTPUT_DIR, f"{item['fname']}.rss")
    ydl = yt_dlp.YoutubeDL()
    info = ydl.extract_info(url, download=False, process=False)
    try:
        with open(archive_file, "r") as f:
            archive = set(f.read().splitlines())
    except FileNotFoundError:
        logging.info("No archive file found.")
        archive = set([])
    if os.path.isfile(pickle_file):
        # https://github.com/lkiesow/python-feedgen/issues/72
        # Workaround for podgen not being able to load from existing rss
        # file.
        logging.info("Loading existing Podcast object from pickle file")
        with open(pickle_file, "rb") as f:
            pod = pickle.load(f)
    else:
        logging.info("No existing pickle found. Create new Podcast object")
        pod = Podcast()
        pod.name = title
        pod.website = url
        pod.description = desc
        pod.explicit = False
        pod.image = item["image"]

    episode_counter = 0
    for e in info["entries"]:
        # The information returned has entries for both "episodes" and
        # "seasons". Only episodes have an "id" key, so we use that to
        # only process the episodes.
        if "id" in e.keys():
            episode_counter = episode_counter + 1
            logging.info(f"Ep counter is at {episode_counter}")
            if e["url"] in archive:
                logging.info(
                    f"Skipping episode {e['url']}, due to already being in archive."
                )
            else:
                try:
                    episode_info = ydl.extract_info(
                        e["url"], download=False, process=True
                    )
                except yt_dlp.utils.DownloadError as error:
                    logging.error(f"{title} - Failed to download {e['id']}")
                    logging.info(error)
                else:
                    ep = Episode()
                    ep.title = episode_info["title"]
                    ep.summary = episode_info.get("summary", "")
                    ep.media = Media

                    request = urllib.request.Request(episode_info["url"], method="HEAD")
                    response = urllib.request.urlopen(request)
                    ep.media = Media(
                        episode_info["url"],
                        size=response.headers["Content-Length"],
                    )
                    ep.publication_date = datetime.datetime.fromtimestamp(
                        episode_info["timestamp"],
                        tz=pytz.timezone("Europe/Oslo"),
                    )
                    ep.image = episode_info["thumbnail"]
                    pod.add_episode(ep)
                    pod.rss_file(os.path.join(rss_file), encoding="UTF-8")
                    with open(archive_file, "a") as f:
                        f.write(e["url"] + "\n")
                    with open(pickle_file, "wb") as f:
                        pickle.dump(pod, f)

        if episode_counter >= int(config["podcasts"]["ep_count"]):
            logging.info("Finishing due to reaching episode count.")
            break


def main():
    logging.basicConfig(level=config["logging"]["level"])

    with open(os.path.join(CONFIG_DIR, "config.json"), "r") as f:
        podcasts = json.load(f)

    while True:
        refresh_start = time.perf_counter()
        threads: list[threading.Thread] = []
        for item in podcasts:
            t = threading.Thread(target=update_podcast, args=(item,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        refresh_duration = time.perf_counter() - refresh_start

        sleep_duration = max(
            [int(config["updates"]["frequency_sec"]) - refresh_duration, 0]
        )
        logging.info(
            f"Refresh finished in {refresh_duration:.3f} seconds. Next refresh in {sleep_duration:.3f} seconds."
        )
        time.sleep(sleep_duration)


if __name__ == "__main__":
    main()
