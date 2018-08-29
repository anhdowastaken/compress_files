import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

import os
import signal
import getopt
import logging
import zipfile
import tarfile

formater = logging.Formatter("[%(asctime)s][%(filename)s:%(lineno)5s] %(levelname)8s --- %(message)s")
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(formater)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

CONFIG_FILE_PATH = "config.ini"

class Config:
    input_files = []
    output_file = ""
    archive_type = ""
    compress_level = 1

    def load(self, config_file):
        if PY2:
            from ConfigParser import SafeConfigParser
            config = SafeConfigParser()
        else:
            import configparser
            config = configparser.ConfigParser()

        try:
            logger.debug("Read {}".format(config_file))

            config.read(config_file)

            self.input_files = config.get("app", "input_files").split(",")
            for s in self.input_files:
                s = s.strip()
            if len(self.input_files) == 0:
                logger.error("Input files are invalid")
                return False

            self.output_file = config.get("app", "output_file")
            if self.output_file == "":
                logger.error("Output file {} is invalid".format(self.output_file))

            self.archive_type = config.get("app", "archive_type")
            if self.archive_type not in ["tar", "tar.gz", "tgz", "gz", "bz2", "xz", "zip"]:
                logger.error("Archive type {} is invalid".format(self.archive_type))
                return False

            self.compress_level = config.getint("app", "compress_level")
            if self.compress_level <= 0:
                logger.error("Compress level {} is invalid".format(self.compress_level))
                return False

            return True
        except Exception as e:
            logger.error(e)
            logger.error("Config file {} in invalid".format(config_file))
            return False

def exit(ret):
    logger.info("----- FINISH -----")
    sys.exit(ret)

config = Config()
config_file = ""

def sighup_handler(signum, frame):
    global config
    tmp = Config()
    if tmp.load(config_file):
        config = tmp

def main(argv):
    try:
        opts, _ = getopt.getopt(argv, "hc", ["config="])
    except Exception as e:
        if getattr(sys, "frozen", False):
            # we are running in a bundle
            print("compress [-c|--config <config_file>]")
        else:
            # we are running in a normal Python environment
            print("compress.py [-c|--config <config_file>]")
        sys.exit(0)

    global config_file
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            if getattr(sys, "frozen", False):
                print("compress [-c|--config <config_file>]")
            else:
                print("compress.py [-c|--config <config_file>]")
            sys.exit(0)
        elif opt in ("-c", "--config"):
            config_file = arg

    logger.info("----- START -----")
    if config_file == "":
        if getattr(sys, "frozen", False):
            bundle_dir = os.path.dirname(sys.executable)
        else:
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(bundle_dir, CONFIG_FILE_PATH)

    # Load configuration file
    if not config.load(config_file):
        exit(1)

    signal.signal(signal.SIGHUP, sighup_handler)

    if config.archive_type == "zip":
        with zipfile.ZipFile(config.output_file, "w") as archive_file:
            for f in config.input_files:
                archive_file.write(f)

        for _ in range(1, config.compress_level):
            with zipfile.ZipFile(config.output_file + ".tmp", "w") as archive_file:
                archive_file.write(config.output_file)
            os.rename(config.output_file + ".tmp", config.output_file)

    else:
        if config.archive_type == "tar":
            write_mode = "w:"
        elif config.archive_type == "tar.gz" or config.archive_type == "tgz" or config.archive_type == "gz":
            write_mode = "w:gz"
        elif config.archive_type == "bz2":
            write_mode = "w:bz2"
        elif config.archive_type == "xz":
            write_mode = "w:xz"

        archive_file = tarfile.open(config.output_file, write_mode)
        for f in config.input_files:
            archive_file.add(f)
        archive_file.close()

        for _ in range(1, config.compress_level):
            archive_file = tarfile.open(config.output_file + ".tmp", write_mode)
            archive_file.add(config.output_file)
            archive_file.close()
            os.rename(config.output_file + ".tmp", config.output_file)

    exit(0)

if __name__ == "__main__":
    argv = sys.argv[1:]
    main(argv)
