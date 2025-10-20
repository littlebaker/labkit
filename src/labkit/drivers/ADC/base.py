from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, Sequence

import numpy as np


TriggerMode = Literal["immediate", "external", "software"]
TriggerEdge = Literal["rising", "falling"]


@dataclass(slots=True)
class DemodulatedRecord:
    """Container for a single demodulated record.

    Attributes
    ----------
    frequency_hz: float
        Demodulation frequency of this record.
    i: np.ndarray
        In-phase component array. Shape: (num_samples,) or (records, num_samples).
    q: np.ndarray
        Quadrature component array. Shape must match ``i``.
    t_s: np.ndarray | None
        Optional time axis in seconds matching the last dimension of ``i``/``q``.
    metadata: Mapping[str, object] | None
        Optional per-record metadata from the device/driver.
    """

    frequency_hz: float
    i: np.ndarray
    q: np.ndarray
    t_s: np.ndarray | None = None
    metadata: Mapping[str, object] | None = None


class ADCBase(ABC):
    """Abstract base class for ADC drivers.

    Implementations should provide configuration for trigger, acquisition, and
    demodulation, and must expose methods to retrieve raw and demodulated data.
    """

    # ----------------------------
    # Trigger configuration
    # ----------------------------
    @abstractmethod
    def configure_trigger(
        self,
        *,
        mode: TriggerMode = "immediate",
        level: float | None = None,
        edge: TriggerEdge | None = None,
        source: str | None = None,
        delay_s: float | None = None,
    ) -> None:
        """Configure the trigger.

        Parameters
        ----------
        mode: {"immediate", "external", "software"}
            Trigger mode.
        level: float | None
            Trigger level in volts (if supported by the device and mode).
        edge: {"rising", "falling"} | None
            Trigger edge (if applicable).
        source: str | None
            Hardware source identifier for external trigger (if applicable).
        delay_s: float | None
            Trigger delay in seconds applied after the trigger fires.
        """
        raise NotImplementedError

    # ----------------------------
    # Acquisition configuration
    # ----------------------------
    @abstractmethod
    def configure_acquisition(
        self,
        *,
        sampling_rate_hz: float | None = None,
        record_length: int | None = None,
        acquisition_time_s: float | None = None,
        num_records: int | None = None,
        channels: Sequence[int] | None = None,
    ) -> None:
        """Configure acquisition timing and size.

        Provide either (sampling_rate_hz and record_length) or acquisition_time_s.
        Drivers should validate combinations based on device constraints.
        """
        raise NotImplementedError

    # ----------------------------
    # Demodulation configuration
    # ----------------------------
    @abstractmethod
    def set_demod_frequencies(self, frequencies_hz: Sequence[float]) -> None:
        """Set the list of demodulation frequencies in Hz."""
        raise NotImplementedError

    # ----------------------------
    # Control
    # ----------------------------
    def arm(self) -> None:
        """Prepare the device for the next acquisition (optional to override)."""

    def start(self) -> None:
        """Start acquisition immediately (optional to override)."""

    def trigger_software(self) -> None:
        """Issue a software trigger (optional to override)."""

    # ----------------------------
    # Data access
    # ----------------------------
    @abstractmethod
    def get_raw_data(self, *, channel: int | None = None) -> np.ndarray:
        """Return raw ADC data.

        Returns an array with shape (num_samples,) for single-shot single-channel
        or (channels, num_samples) / (records, channels, num_samples) depending
        on device and configuration. Implementations must document the shape.
        """
        raise NotImplementedError

    @abstractmethod
    def get_demodulated_data(self) -> Iterable[DemodulatedRecord]:
        """Return an iterable of demodulated records, one per frequency.

        Each record contains I/Q arrays for that frequency and an optional time axis.
        """
        raise NotImplementedError


