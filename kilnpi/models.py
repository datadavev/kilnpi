"""
Models for instruments and readings
"""

import math
import time
import typing

import sqlmodel


def tnow():
    return time.time()

def tnowint():
    return round(time.time())

class SensorType(sqlmodel.SQLModel, table=True):
    id: typing.Optional[str] = sqlmodel.Field(default=None, primary_key=True)
    tcreated: float = sqlmodel.Field(default_factory=tnow)
    tmodified: float = sqlmodel.Field(default_factory=tnow)
    name: str
    units: str
    range_min: typing.Optional[float] = sqlmodel.Field(default=0.0)
    range_max: typing.Optional[float] = sqlmodel.Field(default=1.0)
    missing: typing.Optional[float] = sqlmodel.Field(default=math.nan)
    meta: typing.Optional[dict] = sqlmodel.Field(
        default={}, sa_column=sqlmodel.Column(sqlmodel.JSON)
    )


class InstrumentSensor(sqlmodel.SQLModel, table=True):
    """
    InstrumentTypes have SensorTypes
    """

    sensortype_id: typing.Optional[str] = sqlmodel.Field(
        default=None, foreign_key="sensortype.id", primary_key=True
    )
    instrumenttype_id: typing.Optional[str] = sqlmodel.Field(
        default=None, foreign_key="instrumenttype.id", primary_key=True
    )


class InstrumentType(sqlmodel.SQLModel, table=True):
    id: typing.Optional[str] = sqlmodel.Field(default=None, primary_key=True)
    tcreated: float = sqlmodel.Field(default_factory=tnow)
    tmodified: float = sqlmodel.Field(default_factory=tnow)
    meta: typing.Optional[dict] = sqlmodel.Field(
        default={}, sa_column=sqlmodel.Column(sqlmodel.JSON)
    )


class Instrument(sqlmodel.SQLModel, table=True):
    """
    An instance of an InstrumentType.
    """

    id: typing.Optional[str] = sqlmodel.Field(default=None, primary_key=True)
    type_id: typing.Optional[int] = sqlmodel.Field(
        default=None, foreign_key="instrumenttype.id"
    )
    tcreated: float = sqlmodel.Field(default_factory=tnow)
    tmodified: float = sqlmodel.Field(default_factory=tnow)
    name: str
    meta: typing.Optional[dict] = sqlmodel.Field(
        default={}, sa_column=sqlmodel.Column(sqlmodel.JSON)
    )


class Measurement(sqlmodel.SQLModel, table=True):
    """
    Measurement is the value of a sensor of an instrument at a time.
    """

    id: typing.Optional[str] = sqlmodel.Field(default=None, primary_key=True)
    instrument_id: typing.Optional[str] = sqlmodel.Field(
        default=None, foreign_key="instrument.id"
    )
    sensor_id: typing.Optional[str] = sqlmodel.Field(
        default=None, foreign_key="sensortype.id"
    )
    t: int = sqlmodel.Field(index=True, default_factory=tnowint)
    v: float


class SystemState(sqlmodel.SQLModel, table=True):
    id: typing.Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    tcreated: float = sqlmodel.Field(default_factory=tnow)
    tmodified: float = sqlmodel.Field(default_factory=tnow)
    name: str
    meta: dict = sqlmodel.Field(default={}, sa_column=sqlmodel.Column(sqlmodel.JSON))


def create_db(engine):
    sqlmodel.SQLModel.metadata.create_all(engine)


def get_engine(db_fname: str):
    db_url = f"sqlite:///{db_fname}"
    return sqlmodel.create_engine(db_url)
