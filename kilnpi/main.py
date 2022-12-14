"""

"""

import click
import logging
import logging.config
import kilnpi.models
import sqlmodel

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(name)s:%(levelname)s: %(message)s",
            "dateformat": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propogate": False,
        },
    },
}

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.CRITICAL,
    "CRITICAL": logging.CRITICAL,
}


def getLogger():
    return logging.getLogger("kilnpi")


@click.group()
@click.pass_context
@click.option("-s", "--store", default="kilnpi.db", help="SQLite db for kilnpi")
@click.option("--verbosity", default="INFO", help="Logging level")
def main(ctx, store, verbosity) -> int:
    verbosity = verbosity.upper()
    logging_config["loggers"][""]["level"] = verbosity
    logging.config.dictConfig(logging_config)
    L = getLogger()
    ctx.ensure_object(dict)
    L.info("Using store at: %s", store)
    ctx.obj["store_fname"] = store
    return 0


@main.command("init")
@click.pass_context
def initialize(ctx):
    L = getLogger()
    L.info("Creating datastore at: %s", ctx.obj["store_fname"])
    engine = kilnpi.models.get_engine(ctx.obj["store_fname"])
    kilnpi.models.create_db(engine)

    with sqlmodel.Session(engine) as session:
        session.add(kilnpi.models.SensorType(
            id="DHT22_T",
            name="Temperature",
            units="C",
            range_min=-20.0,
            range_max=100.0
        ))
        session.add(kilnpi.models.SensorType(
            id="DHT22_RH",
            name="Relative Humidity",
            units="%",
            range_min=0.0,
            range_max=100.0
        ))
        session.add(kilnpi.models.InstrumentType(
            id="DHT22",
            _created=kilnpi.models.tnow(),
            _modified=kilnpi.models.tnow(),
        ))
        session.add(kilnpi.models.InstrumentSensor(
            sensortype_id="DHT22_T",
            instrumenttype_id="DHT22"
        ))
        session.add(kilnpi.models.InstrumentSensor(
            sensortype_id="DHT22_RH",
            instrumenttype_id="DHT22"
        ))
        session.commit()

    L.info("Done.")
