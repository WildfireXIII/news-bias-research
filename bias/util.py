""" Utility functions for jupyter notebooks """

import logging
import os
import pickle
import re
import sqlite3
import inspect
import sys
import json

import pandas as pd

TMP_PATH = None

DATA_RAW_PATH = "../data/raw/"

GT_COLS = {
    "NewsGuard": [
        "NewsGuard, Does not repeatedly publish false content",
        "NewsGuard, Gathers and presents information responsibly",
        "NewsGuard, Regularly corrects or clarifies errors",
        "NewsGuard, Handles the difference between news and opinion responsibly",
        "NewsGuard, Avoids deceptive headlines",
        "NewsGuard, Website discloses ownership and financing",
        "NewsGuard, Clearly labels advertising",
        "NewsGuard, Reveals who's in charge, including any possible conflicts of interest",
        "NewsGuard, Provides information about content creators",
        "NewsGuard, score",
        "NewsGuard, overall_class",
    ],
    "Pew Research Center": [
        "Pew Research Center, known_by_40%",
        "Pew Research Center, total",
        "Pew Research Center, consistently_liberal",
        "Pew Research Center, mostly_liberal",
        "Pew Research Center, mixed",
        "Pew Research Center, mostly conservative",
        "Pew Research Center, consistently conservative",
    ],
    "Wikipedia": ["Wikipedia, is_fake"],
    "Open Sources": [
        "Open Sources, reliable",
        "Open Sources, fake",
        "Open Sources, unreliable",
        "Open Sources, bias",
        "Open Sources, conspiracy",
        "Open Sources, hate",
        "Open Sources, junksci",
        "Open Sources, rumor",
        "Open Sources, blog",
        "Open Sources, clickbait",
        "Open Sources, political",
        "Open Sources, satire",
        "Open Sources, state",
    ],
    "Media Bias / Fact Check": [
        "Media Bias / Fact Check, label",
        "Media Bias / Fact Check, factual_reporting",
        "Media Bias / Fact Check, extreme_left",
        "Media Bias / Fact Check, right",
        "Media Bias / Fact Check, extreme_right",
        "Media Bias / Fact Check, propaganda",
        "Media Bias / Fact Check, fake_news",
        "Media Bias / Fact Check, some_fake_news",
        "Media Bias / Fact Check, failed_fact_checks",
        "Media Bias / Fact Check, conspiracy",
        "Media Bias / Fact Check, pseudoscience",
        "Media Bias / Fact Check, hate_group",
        "Media Bias / Fact Check, anti_islam",
        "Media Bias / Fact Check, nationalism",
    ],
    "Allsides": [
        "Allsides, bias_rating",
        "Allsides, community_agree",
        "Allsides, community_disagree",
        "Allsides, community_label",
    ],
    "BuzzFeed": ["BuzzFeed, leaning"],
    "Politifact": [
        "PolitiFact, Pants on Fire!",
        "PolitiFact, False",
        "PolitiFact, Mostly False",
        "PolitiFact, Half-True",
        "PolitiFact, Mostly True",
        "PolitiFact, True",
    ],
}

# The dictionary of source names that are actually the same, but differ textually between MBC and NELA
MBC_to_NELA = {
    "New York Times": "The New York Times",
    "Wall Street Journal": "WSJ Washington Wire",
    "ABC": "ABC News",
    "Washington Examiner": "The Washington Examiner",
    "The Blaze": "TheBlaze",
    "BuzzFeed": "Buzzfeed",
    "Mother Jones": "MotherJones",
    "National Public Radio": "NPR",
    "The New Yorker": "New Yorker",
    "Huffington Post": "The Huffington Post",
    "Intercept": "The Intercept",
    "Daily Caller": "The Daily Caller",
    "Fiscal Times": "The Fiscal Times",
    "ShareBlue": "Shareblue",
    "InfoWars": "Infowars",
    "Think Progress": "ThinkProgress",
    "CBS": "CBS News"
}


def nela_load_labels():
    labels_df = pd.read_csv(os.path.join(DATA_RAW_PATH, "nela", "labels.csv"))
    labels_df = labels_df.rename(columns={"Unnamed: 0": "Source"})
    return labels_df


def nela_load_media_bias_monitor():
    with open("../data/raw/nela_sources_alt.json", "r") as infile:
        data = json.load(infile)
    return data


def nela_labels_gtsource(labels_df, gt_source):
    """ only return label columns from specified ground truth source """
    return labels_df[GT_COLS[gt_source]]


def load_dataset(cache_path):
    with open("../data/cache/" + cache_path, "rb") as infile:
        obj = pickle.load(infile)
    return obj


def load_selection_dataset(name):
    # return pd.read_csv("../data/cache/" + name)
    return pd.read_pickle("../data/cache/" + name)


def load_fold_divisions_dataset(selection_tag="", bias=True):
    if bias:
        with open(f"../data/cache/{selection_tag}folds_selection.json", 'r') as infile:
            folds = json.load(infile)
    else:
        print(f"../data/cache/{selection_tag}reliability_folds_selection.json")
        with open(f"../data/cache/{selection_tag}reliability_folds_selection.json", 'r') as infile:
            folds = json.load(infile)
    return folds


def load_scraped_mpc():
    return pd.read_pickle("../data/raw/mbc_scraped.pkl")


# pass count of -1 for all articles from source
# can't run on cluster
def nela_load_articles_from_source(source_name, count=-1):
    conn = sqlite3.connect("../data/raw/nela/articles.db")

    count_string = ""
    if count != -1:
        count_string = "limit " + str(count)

    df = pd.read_sql_query(
        "SELECT * FROM articles WHERE source='"
        + str(source_name)
        + "' "
        + count_string
        + ";",
        conn,
    )
    return df


def nela_count_articles_from_source(source_name):
    conn = sqlite3.connect("../data/raw/nela/articles.db")
    df = pd.read_sql_query(
        "SELECT COUNT(*) FROM articles WHERE source='" + str(source_name) + "';", conn
    )
    return df


def stack_dfs(df1, df2):
    """ Appends df2 to the end of df1, but assigns df2 to df1 if df1 is None """
    if df1 is None:
        df1 = df2
    else:
        df1 = df1.append(df2, ignore_index=True)

    return df1


def clean_newlines(content):
    content = re.sub("(\r\n)+", " ", str(content))
    return content


def clean_symbols(content):
    content = re.sub(r'[\!"#$%&\*+,-./:;<=>?@^_`()|~=]', "", content)
    return content


def check_output_necessary(output_path, overwrite):
    """Determine whether a step is necessary by checking for its existence/overwrite combo.

    Returns true if should continue with step, false if can skip.
    """

    logging.debug("Checking for existence of '%s'...", output_path)

    if os.path.exists(output_path):
        logging.debug("Output found.")
        logging.info("Cached version found.")

        # check if should overwite the existing output or not
        if overwrite:
            logging.debug("Overwrite requested, continuing...")
            logging.warning("Overwriting an existing output '%s'!", output_path)
            return True

        logging.debug("No overwrite requested, skip step...")
        return False

    # if this point hit, the file doesn't exist yet
    return True


def init_logging(log_path=None):
    """Sets up logging config, including associated file output."""
    log_formatter = logging.Formatter(
        "%(asctime)s - %(filename)s - %(levelname)s - %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if log_path is not None:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def create_dir(path):
    try:
        os.mkdir(path)
    except:
        logging.warning("Did not create directory %s", path)


def dump_log(func):
    """Decorator to print function call details - parameters names and effective values."""
    def wrapper(*args, **kwargs):
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str =  ', '.join('{} = {!r}'.format(*item) for item in func_args.items())
        logging.info(f'CALL::{func.__module__}.{func.__qualname__}({func_args_str})')
        return func(*args, **kwargs)
    return wrapper
