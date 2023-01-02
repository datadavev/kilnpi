'''
Fan controller for the kiln.

Fans are connected to relays 1, 2, and 3 on a 6 relay board:
https://github.com/sbcshop/Pirelay-6-Channel


'''

import logging
import logging.config
import click
import RPi.GPIO

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


FAN_CONFIG = {
    1: 29,
    2: 31,
    3: 33
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

def get_logger():
    return logging.getLogger("kilnpi")


def get_fan(fan_id:int):
    _pin = FAN_CONFIG[fan_id]
    RPi.GPIO.setup(_pin, RPi.GPIO.IN)
    status = RPi.GPIO.input(_pin)
    return status


def start_fan(fan_id:int):
    _pin = FAN_CONFIG[fan_id]
    RPi.GPIO.setup(_pin, RPi.GPIO.OUT)
    RPi.GPIO.output(_pin, RPi.GPIO.HIGH)


def stop_fan(fan_id:int):
    _pin = FAN_CONFIG[fan_id]
    RPi.GPIO.setup(_pin, RPi.GPIO.OUT)
    RPi.GPIO.output(_pin, RPi.GPIO.LOW)



@click.group()
@click.pass_context
@click.option("--verbosity", default="INFO", help="Logging level")
def main(ctx, verbosity):
    verbosity = verbosity.upper()
    logging_config["loggers"][""]["level"] = verbosity
    logging.config.dictConfig(logging_config)
    L = get_logger()
    ctx.ensure_object(dict)


@main.command("start")
@click.pass_context
@click.argument("fans", nargs=-1)
def start_fans(ctx, fans):
    L = get_logger()
    RPi.GPIO.setmode(RPi.GPIO.BOARD)

    for fan in fans:
        fan_id = int(fan)
        if fan_id < 1 or fan_id > 3:
            L.error("Invalid fan id: %s", fan_id)
            continue
        L.info("Starting fan %s", fan_id)
        start_fan(fan_id)
    RPi.GPIO.cleanup()


@main.command("stop")
@click.pass_context
@click.argument("fans", nargs=-1)
def stop_fans(ctx, fans):
    L = get_logger()
    RPi.GPIO.setmode(RPi.GPIO.BOARD)

    for fan in fans:
        fan_id = int(fan)
        if fan_id < 1 or fan_id > 3:
            L.error("Invalid fan id: %s", fan_id)
            continue
        L.info("Stopping fan %s", fan_id)
        stop_fan(fan_id)
    RPi.GPIO.cleanup()


@main.command("status")
@click.pass_context
@click.argument("fans", nargs=-1)
def get_fans(ctx, fans):
    L = get_logger()
    RPi.GPIO.setmode(RPi.GPIO.BOARD)

    for fan in fans:
        fan_id = int(fan)
        if fan_id < 1 or fan_id > 3:
            L.error("Invalid fan id: %s", fan_id)
            continue
        status = get_fan(fan_id)
        print(f"Fan {fan_id} status: {status}")
    RPi.GPIO.cleanup()

if __name__ == "__main__":
    main()
