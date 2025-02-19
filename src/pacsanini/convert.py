# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The convert module provides utility methods that can be used
to convert raw DICOM data to DICOM files.
"""
import json
import re

from datetime import datetime, timedelta
from typing import Dict, Union

from pydicom import Dataset, dcmread


def str2datetime(dcm_date: str) -> datetime:
    """Parse a date in DICOM string format and return
    a datetime object.

    Strings can come in the following formats:
    YYYYMMDD (date), or YYYYMMDDHHMMSS.FFFFFF&ZZXX
    (datetime) -as specified by the DICOM standard.

    Parameters
    ----------
    dcm_date : str
        A date(time) in DICOM string format.

    Returns
    -------
    datetime
        A datetime corresponding to the DICOM string
        value.

    Raises
    ------
    ValueError
        A ValueError is raised if the dcm_date parameter
        does not conform to any DICOM date(time) format.
    """
    fmt = "%Y%m%d"
    try:
        return datetime.strptime(dcm_date, fmt)
    except ValueError:
        fmt += "%H%M%S.%f"
        try:
            return datetime.strptime(dcm_date, fmt)
        except ValueError:
            fmt += "%z"
            return datetime.strptime(dcm_date, fmt)


def str2timedelta(dcm_time: str) -> timedelta:
    """Parse a time in DICOM string value and return a
    timedelta object.

    Time strings in DICOM format are formatted in the
    following way: HHMMSS.FFFFFF. The only mandatory
    component in DICOM time strings is the hour component.

    Parameters
    ----------
    dcm_time : str
        A time value in DICOM string format.

    Returns
    -------
    timedelta
        The DICOM time value as a timedelta object.

    Raises
    ------
    ValueError
        A ValueError is raised if the dcm_time parameter
        does not conform to the DICOM time format.
    """
    m = re.fullmatch(
        r"(\d\d)(?:(\d\d)(?:(\d\d)(?:\.(\d{1,6}))?)?)?", dcm_time, flags=re.ASCII
    )

    if m is None:
        raise ValueError(f"Invalid DICOM time string: '{dcm_time}'")

    time_vals = {"hours": int(m.group(1))}
    if m.group(2) is not None:
        time_vals["minutes"] = int(m.group(2))
        if m.group(3) is not None:
            time_vals["seconds"] = int(m.group(3))
            if m.group(4) is not None:
                time_vals["microseconds"] = int(m.group(4).ljust(6, "0"))

    return timedelta(**time_vals)


def datetime2str(date_time: datetime, use_time: bool = False) -> str:
    """Convert a datetime object to a DICOM compliant date(time) string.

    Parameters
    ----------
    date_time : datetime
        The datetime object to convert ot a DICOM string.
    use_time : bool
        If False, the default, don't add the time component in the
        return value. Note that this has no impact if the datetime
        component has an existing time component.

    Returns
    -------
    str
        The datetime object as a DICOM string.
    """
    omit_time = (
        date_time.hour == 0
        and date_time.minute == 0
        and date_time.second == 0
        and date_time.microsecond == 0
    )

    if use_time or not omit_time:
        if date_time.tzinfo is not None:
            return date_time.strftime("%Y%m%d%H%M%S.%f%z")
        return date_time.strftime("%Y%m%d%H%M%S.%f")
    return date_time.strftime("%Y%m%d")


def timedelta2str(time_delta: timedelta) -> str:
    """Convert a timedelta object to its DICOM string counterpart.

    Parameters
    ----------
    time_delta : timedelta
        The timedelta object to convert to string.

    Returns
    -------
    str
        The timdelta objected represented as a DICOM time string.
    """
    ref_date = datetime(1970, 1, 1) + time_delta
    return ref_date.strftime("%H%M%S.%f")


def dcm2dict(dcm: Union[Dataset, str], include_pixels: bool = False) -> Dict[str, dict]:
    """Return the JSON-compatiable dict representation of a DICOM file.

    Parameters
    ----------
    dcm : Union[Dataset, str]
        The DICOM Dataset or file path to convert to use in order to produce
        the JSON dict.
    include_pixels : bool
        If True, include the pixel array in the generated dict. The default
        is False.

    Returns
    -------
    dict
        A JSON-compatible dict representation of the DICOM.
    """
    if isinstance(dcm, str):
        dcm = dcmread(dcm, stop_before_pixels=not include_pixels)
    if not include_pixels:
        dcm.PixelData = None

    dcm_dict = dcm.to_json_dict()
    for key, value in dcm_dict.items():
        tag_name = dcm[key].name.replace("[", "").replace("]", "")
        tag_name = "".join(char.capitalize() for char in tag_name.split(" "))
        value["Name"] = tag_name

    return dcm_dict


def dict2dcm(dcm_dict: Dict[str, dict]) -> Dataset:
    """Convert a dictionary containing DICOM tag metadata to a DICOM Dataset.

    Parameters
    ----------
    dcm_dict : Dict[str, dict]
        A dictionary containg DICOM tag metadata that you want to
        convert to a Dataset.

    Returns
    -------
    Dataset
        The DICOM Dataset.
    """
    for values in dcm_dict.values():
        values.pop("Name", None)

    return Dataset.from_json(json.dumps(dcm_dict))
