"""Implement pynvml interface using rocmi pure python lib"""

# pylint: disable=protected-access

import atexit
import functools
import os
import sys
import textwrap
import warnings

from collections import namedtuple

import rocmi


NVML_TEMPERATURE_GPU = 1


class NVMLError(Exception):
    pass


class NVMLError_Unknown(Exception):
    pass


class NVMLError_GpuIsLost(Exception):
    pass


def nvmlDeviceGetCount():
    return len(rocmi.get_devices())


def nvmlDeviceGetHandleByIndex(dev):
    return rocmi.get_devices()[dev]


def nvmlDeviceGetIndex(handle):
    for i, d in enumerate(rocmi.get_devices()):
        if d.bus_id == handle.bus_id:
            return i

    return -1


def nvmlDeviceGetName(handle):
    return handle.name


def nvmlDeviceGetUUID(handle):
    return handle.unique_id


def nvmlDeviceGetTemperature(handle, loc=NVML_TEMPERATURE_GPU):
    metrics = handle.get_metrics()
    return metrics.temperature_hotspot


def nvmlSystemGetDriverVersion():
    return ""


def check_driver_nvml_version(driver_version_str: str):
    pass


def nvmlDeviceGetFanSpeed(handle):
    try:
        speed = handle.get_metrics().current_fan_speed
    except AttributeError:
        return None

    return speed


MemoryInfo = namedtuple("MemoryInfo", ["total", "used"])


def nvmlDeviceGetMemoryInfo(handle):

    return MemoryInfo(
        total=handle.vram_total,
        used=handle.vram_used,
    )


UtilizationRates = namedtuple("UtilizationRates", ["gpu"])


def nvmlDeviceGetUtilizationRates(handle):
    metrics = handle.get_metrics()
    return UtilizationRates(gpu=metrics.average_gfx_activity)


def nvmlDeviceGetEncoderUtilization(dev):
    return None


def nvmlDeviceGetDecoderUtilization(dev):
    return None


def nvmlDeviceGetPowerUsage(handle):
    return handle.current_power / 1000000


def nvmlDeviceGetEnforcedPowerLimit(handle):
    return handle.power_limit / 1000000


def nvmlDeviceGetComputeRunningProcesses(dev):
    return rocmi.get_processes_for(dev)


def nvmlDeviceGetGraphicsRunningProcesses(dev):
    return None


def nvmlDeviceGetClkFreq(handle):
    metrics = handle.get_metrics()

    try:
        clk = metrics.current_gfxclks[0]
    except AttributeError:
        clk = metrics.current_gfxclk

    return clk


def nvmlDeviceGetClkFreqMax(handle):
    return handle.get_clock_info()[-1]


def ensure_initialized():
    pass
