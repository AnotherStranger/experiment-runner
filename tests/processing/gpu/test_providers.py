"""
Class for testing running with and without 'nvidia-smi'
"""

import os
from unittest.mock import MagicMock

import pytest

from experiment_runner.processing.gpu.exceptions import GPUNotFoundException
from experiment_runner.processing.gpu.models import GPU, GPUProcess
from experiment_runner.processing.gpu.providers import NvidiaGPUProvider


@pytest.fixture
def nvidia_smi_gpu_output_csv():
    return str(
        "0, GPU-8bfb8a55-1787-40ee-38fc-fe4af7dfdb6c, 0, 49152, 1, 48592, 535.104.05, Quadro RTX 8000, 1324821109943, Disabled, Disabled, 35"
        + os.linesep
        + "1, GPU-3b91b854-3dfa-fa53-5612-52ccda6d8f2a, 0, 49152, 48353, 231, 535.104.05, Quadro RTX 8000, 1324821109359, Disabled, Disabled, 49"
        + os.linesep
        + "2, GPU-5139bf4a-32d0-a429-d3b8-be21a674e15f, 0, 49152, 48373, 219, 535.104.05, Quadro RTX 8000, 1324021077931, Disabled, Disabled, 50"
        + os.linesep
    )


def setup_subprocess_run_mock(mocker, nvidia_smi_gpu_output_csv):
    mock = mocker.patch("subprocess.run")
    mock_output = nvidia_smi_gpu_output_csv
    """
    Configure the Mock
    """
    property_mock = MagicMock()
    property_mock.configure_mock(stdout=mock_output)
    mock.return_value = property_mock
    return mock


def test_providers_without_nvidia_smi(mocker):
    """
    Function to test _run_nvidia_smi without 'nvidia-smi'
    """
    mock = mocker.patch("subprocess.run")
    error_message = "🚨 File 'nvidia-smi' not found. 🚨"

    mock.side_effect = FileNotFoundError(error_message)
    mock_obj = NvidiaGPUProvider()

    with pytest.raises(GPUNotFoundException) as ex_info:
        mock_obj._run_nvidia_smi([])

    assert str(ex_info.value) == error_message


def test_providers_with_nvidia_smi(mocker, nvidia_smi_gpu_output_csv):
    """
    Function to test _run_nvidia_smi with 'nvidia-smi'
    """
    setup_subprocess_run_mock(mocker, nvidia_smi_gpu_output_csv)

    mock_obj = NvidiaGPUProvider()
    # This converts csv-reader into a list
    result = list(mock_obj._run_nvidia_smi([]))
    """
    Expect that results are the same
    """
    expected_result = [
        [
            "0",
            " GPU-8bfb8a55-1787-40ee-38fc-fe4af7dfdb6c",
            " 0",
            " 49152",
            " 1",
            " 48592",
            " 535.104.05",
            " Quadro RTX 8000",
            " 1324821109943",
            " Disabled",
            " Disabled",
            " 35",
        ],
        [
            "1",
            " GPU-3b91b854-3dfa-fa53-5612-52ccda6d8f2a",
            " 0",
            " 49152",
            " 48353",
            " 231",
            " 535.104.05",
            " Quadro RTX 8000",
            " 1324821109359",
            " Disabled",
            " Disabled",
            " 49",
        ],
        [
            "2",
            " GPU-5139bf4a-32d0-a429-d3b8-be21a674e15f",
            " 0",
            " 49152",
            " 48373",
            " 219",
            " 535.104.05",
            " Quadro RTX 8000",
            " 1324021077931",
            " Disabled",
            " Disabled",
            " 50",
        ],
    ]
    assert result == expected_result


def test_get_compute_processes_should_return_empty_list(mocker):
    """
    Function to test get_compute_processes with an empty result
    """
    mock_obj = NvidiaGPUProvider()
    mocker.patch.object(mock_obj, "_run_nvidia_smi", return_value=[])
    result = mock_obj.get_compute_processes()
    assert result == []


def test_get_compute_processes_should_return_gpu(mocker):
    """
    Function to test get_compute_processes
    """
    mock_obj = NvidiaGPUProvider()
    mock_output = [
        ["12809", "/opt/conda/bin/python3.9", "GPU-3b91b854-3dfa-fa53-5612-52ccda6d8f2a"],
        ["12810", "/opt/conda/bin/python3.9", "GPU-5139bf4a-32d0-a429-d3b8-be21a674e15f"],
    ]

    mocker.patch.object(mock_obj, "_run_nvidia_smi", return_value=mock_output)
    """
    Expected Output
    """
    expected_result = [
        GPUProcess(
            pid=12809,
            process_name="/opt/conda/bin/python3.9",
            gpu_uuid="GPU-3b91b854-3dfa-fa53-5612-52ccda6d8f2a",
        ),
        GPUProcess(
            pid=12810,
            process_name="/opt/conda/bin/python3.9",
            gpu_uuid="GPU-5139bf4a-32d0-a429-d3b8-be21a674e15f",
        ),
    ]
    """
    The mock object sets results
    """
    result = mock_obj.get_compute_processes()
    """
    Checks if result has valid GPUProcesses
    """
    for gpu_process in result:
        assert isinstance(gpu_process, GPUProcess)
        assert hasattr(gpu_process, "pid")
        assert hasattr(gpu_process, "process_name")
        assert hasattr(gpu_process, "gpu_uuid")
    """
    Compare the mock-result to the expected
    """
    assert result == expected_result


def test_gpus_should_return_a_empty_list(mocker):
    """
    Function to test if gpus() returns an empty list of installed GPUs
    """
    mock_obj = NvidiaGPUProvider()
    mocker.patch.object(mock_obj, "_run_nvidia_smi", return_value=[])
    result = mock_obj.gpus
    assert result == []


def test_gpus_should_return_installed_gpus(mocker, nvidia_smi_gpu_output_csv):
    """
    Function to test if gpus() returns a list of all installed GPUs
    """
    setup_subprocess_run_mock(mocker, nvidia_smi_gpu_output_csv)
    mock_obj = NvidiaGPUProvider()
    """
    Expected Output for GPUs
    """
    expected_result = [
        GPU(
            id=0,
            uuid="GPU-8bfb8a55-1787-40ee-38fc-fe4af7dfdb6c",
            load=0,
            memory_total=49152,
            memory_used=1,
            memory_free=48592,
            driver="535.104.05",
            name="Quadro RTX 8000",
            serial="1324821109943",
            display_mode="Disabled",
            display_active="Disabled",
            temperature=35,
        ),
        GPU(
            id=1,
            uuid="GPU-3b91b854-3dfa-fa53-5612-52ccda6d8f2a",
            load=0,
            memory_total=49152,
            memory_used=48353,
            memory_free=231,
            driver="535.104.05",
            name="Quadro RTX 8000",
            serial="1324821109359",
            display_mode="Disabled",
            display_active="Disabled",
            temperature=49,
        ),
        GPU(
            id=2,
            uuid="GPU-5139bf4a-32d0-a429-d3b8-be21a674e15f",
            load=0,
            memory_total=49152,
            memory_used=48373,
            memory_free=219,
            driver="535.104.05",
            name="Quadro RTX 8000",
            serial="1324021077931",
            display_mode="Disabled",
            display_active="Disabled",
            temperature=50,
        ),
    ]
    result = mock_obj.gpus
    """
    Checks that the result has valid GPUs
    """
    for gpu in result:
        assert isinstance(gpu, GPU)
        assert hasattr(gpu, "id")
        assert hasattr(gpu, "uuid")
        assert hasattr(gpu, "load")
        assert hasattr(gpu, "memory_total")
        assert hasattr(gpu, "memory_used")
        assert hasattr(gpu, "memory_free")
        assert hasattr(gpu, "driver")
        assert hasattr(gpu, "name")
        assert hasattr(gpu, "serial")
        assert hasattr(gpu, "display_mode")
        assert hasattr(gpu, "display_active")
        assert hasattr(gpu, "temperature")
    """
    Compare the mock-results to the expected
    """
    assert result == expected_result
