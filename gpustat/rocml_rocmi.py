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
    return len(rocmi.iter_devices())


def nvmlDeviceGetHandleByIndex(dev):
    return rocmi.iter_devices()[dev]


def nvmlDeviceGetIndex(handle):
    return handle.id


def nvmlDeviceGetName(handle):
    return rocmi.get_device_info(handle.card).name


def nvmlDeviceGetUUID(handle):
    return rocmi.get_device_info(handle.card).guid


def nvmlDeviceGetTemperature(handle, loc=NVML_TEMPERATURE_GPU):
    di = rocmi.get_device_info(handle.card)
    metrics = di.get_metrics()
    return metrics.temperature_hotspot


def nvmlSystemGetDriverVersion():
    return ""


def check_driver_nvml_version(driver_version_str: str):
    pass


def nvmlDeviceGetFanSpeed(handle):
    di = rocmi.get_device_info(handle.card)
    try:
        speed = di.get_metrics().current_fan_speed
    except AttributeError:
        return None

    return speed


MemoryInfo = namedtuple("MemoryInfo", ["total", "used"])


def nvmlDeviceGetMemoryInfo(handle):
    di = rocmi.get_device_info(handle.card)

    return MemoryInfo(
        total=di.vram_total,
        used=di.vram_used,
    )


UtilizationRates = namedtuple("UtilizationRates", ["gpu"])


def nvmlDeviceGetUtilizationRates(handle):
    di = rocmi.get_device_info(handle.card)
    metrics = di.get_metrics()
    return UtilizationRates(gpu=metrics.average_gfx_activity)


def nvmlDeviceGetEncoderUtilization(dev):
    return None


def nvmlDeviceGetDecoderUtilization(dev):
    return None


def nvmlDeviceGetPowerUsage(handle):
    di = rocmi.get_device_info(handle.card)
    return di.current_power / 1000000


def nvmlDeviceGetEnforcedPowerLimit(handle):
    return rocmi.get_device_info(handle.card).power_limit / 1000000


ComputeProcess = namedtuple("ComputeProcess", ["pid", "usedGpuMemory"])


def nvmlDeviceGetComputeRunningProcesses(dev):
    results = rocmi.get_processes()
    current_procs = [ComputeProcess(pid=x.pid, usedGpuMemory=0) for x in results if dev.gpu_id in rocmi.get_process_gpus(x.pid)]
    return current_procs


def nvmlDeviceGetGraphicsRunningProcesses(dev):
    return None


def nvmlDeviceGetClkFreq(handle):
    di = rocmi.get_device_info(handle.card)
    metrics = di.get_metrics()

    try:
        clk = metrics.current_gfxclks[0]
    except AttributeError:
        clk = metrics.current_gfxclk

    return clk


def nvmlDeviceGetClkFreqMax(handle):
    di = rocmi.get_device_info(handle.card)
    return di.get_clock_info()[-1]


def ensure_initialized():
    pass
