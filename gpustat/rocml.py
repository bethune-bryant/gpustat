"""Imports pyrsmi and wraps it in a pynvml compatible interface."""

# pylint: disable=protected-access

import atexit
import functools
import os
import sys
import textwrap
import warnings

from collections import namedtuple


from amdsmi import *

NVML_TEMPERATURE_GPU = 1

class NVMLError_Unknown(Exception):
    def __init__(self, message="An unknown ROCMLError has occurred"):
        self.message = message
        super().__init__(self.message)

class NVMLError_GpuIsLost(Exception):
    def __init__(self, message="ROCM Device is lost."):
        self.message = message
        super().__init__(self.message)


_stdout_dup = os.dup(1)
_stderr_dup = os.dup(2)
_silent_pipe = os.open(os.devnull, os.O_WRONLY)

def silent_run(to_call, *args, **kwargs):
    os.dup2(_silent_pipe, 1)
    os.dup2(_silent_pipe, 2)
    retval = to_call(*args, **kwargs)
    os.dup2(_stdout_dup, 1)
    os.dup2(_stderr_dup, 2)
    return retval

def nvmlDeviceGetCount():
    return len(amdsmi_get_processor_handles())

def nvmlDeviceGetHandleByIndex(dev):
    return amdsmi_get_processor_handles()[dev]

def nvmlDeviceGetIndex(dev):
    return -1

def nvmlDeviceGetName(dev):
    return amdsmi_get_gpu_board_info(dev)["product_name"]

def nvmlDeviceGetUUID(dev):
    return amdsmi_get_gpu_device_uuid(dev)

def nvmlDeviceGetTemperature(dev, loc=NVML_TEMPERATURE_GPU):
    return amdsmi_get_temp_metric(dev, AmdSmiTemperatureType.HOTSPOT, AmdSmiTemperatureMetric.CURRENT)

def nvmlSystemGetDriverVersion():
    return ""

def check_driver_nvml_version(driver_version_str: str):
    """Show warnings when an incompatible driver is used."""

    def safeint(v) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    driver_version = tuple(safeint(v) for v in
                           driver_version_str.strip().split("."))

    if driver_version < (6, 7, 8):
        warnings.warn(f"This version of ROCM Driver {driver_version_str} is untested, ")

def nvmlDeviceGetFanSpeed(dev):
    try:
        return amdsmi_get_gpu_fan_speed(dev, 0)
    except Exception:
        return None

MemoryInfo = namedtuple('MemoryInfo', ['total', 'used'])

def nvmlDeviceGetMemoryInfo(dev):
    return MemoryInfo(total=amdsmi_get_gpu_memory_total(dev, AmdSmiMemoryType.VRAM),
                      used=amdsmi_get_gpu_memory_usage(dev, AmdSmiMemoryType.VRAM))

UtilizationRates = namedtuple('UtilizationRates', ['gpu'])

def nvmlDeviceGetUtilizationRates(dev):
    return UtilizationRates(gpu=amdsmi_get_gpu_activity(dev)["gfx_activity"])

def nvmlDeviceGetEncoderUtilization(dev):
    return None

def nvmlDeviceGetDecoderUtilization(dev):
    return None

def nvmlDeviceGetPowerUsage(dev):
    return amdsmi_get_power_info(dev)["current_socket_power"]

def nvmlDeviceGetEnforcedPowerLimit(dev):
    return amdsmi_get_power_info(dev)["power_limit"]

ComputeProcess = namedtuple('ComputeProcess', ['pid', 'usedGpuMemory'])

def nvmlDeviceGetComputeRunningProcesses(dev):
    results = amdsmi_get_gpu_process_list(dev)
    return [ComputeProcess(pid=x.pid, usedGpuMemory=x.mem) for x in results]

def nvmlDeviceGetGraphicsRunningProcesses(dev):
    return None

def nvmlDeviceGetClkFreq(dev):
    result = amdsmi_get_clock_info(dev, AmdSmiClkType.SYS)
    if "clk" in result:
        return result["clk"]
    else:
        return result["cur_clk"]

def nvmlDeviceGetClkFreqMax(dev):
    result = amdsmi_get_clock_info(dev, AmdSmiClkType.SYS)
    return result["max_clk"]

# Upon importing this module, let rocml be initialized and remain active
# throughout the lifespan of the python process (until gpustat exists).
_initialized: bool
_init_error = None
try:
    amdsmi_init()
    _initialized = True

    def _shutdown():
        amdsmi_shut_down()
    atexit.register(_shutdown)

except Exception as exc:
    _initialized = False
    _init_error = exc


def ensure_initialized():
    if not _initialized:
        raise _init_error  # type: ignore


