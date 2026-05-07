"""
Per-patient session memory for OncoAgent.

Design inspired by Hermes Agent's persistent memory:
  - Each patient gets an isolated profile with their own clinical history.
  - Memory is scoped per ``patient_id``, never global.
  - Thread-safe via a simple dict-based store (swap for Redis/SQLite
    in production if needed).

Usage:
    store = PatientMemoryStore()
    store.save_interaction(patient_id="P001", interaction={...})
    history = store.get_history(patient_id="P001")
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PatientProfile:
    """Isolated memory profile for a single patient.

    Attributes:
        patient_id: Unique identifier for the patient.
        created_at: ISO timestamp of profile creation.
        interactions: Ordered list of past query/response pairs.
        metadata: Arbitrary metadata (e.g., preferred language).
    """

    patient_id: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_interaction(self, interaction: Dict[str, Any]) -> None:
        """Append an interaction to the patient's history.

        Args:
            interaction: Dict with at minimum ``query`` and ``response`` keys.
        """
        interaction["timestamp"] = datetime.now(timezone.utc).isoformat()
        interaction["interaction_id"] = str(uuid.uuid4())[:8]
        self.interactions.append(interaction)
        logger.debug(
            "Patient %s: stored interaction #%d",
            self.patient_id,
            len(self.interactions),
        )

    def get_recent_context(self, n: int = 3) -> List[Dict[str, Any]]:
        """Return the last *n* interactions for context injection.

        Args:
            n: Number of recent interactions to return.

        Returns:
            List of the most recent interactions (newest last).
        """
        return self.interactions[-n:]

    def summary(self) -> str:
        """Return a brief summary string for logging/UI display."""
        return (
            f"Patient {self.patient_id} | "
            f"{len(self.interactions)} interactions | "
            f"Created: {self.created_at}"
        )


class PatientMemoryStore:
    """In-memory store for per-patient profiles.

    For hackathon scope this uses a simple dict.  In production,
    replace with SQLite / Redis for persistence across restarts.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, PatientProfile] = {}

    def get_or_create_profile(
        self,
        patient_id: Optional[str] = None,
    ) -> PatientProfile:
        """Retrieve an existing profile or create a new one.

        Args:
            patient_id: Existing patient ID. If None, generates a new one.

        Returns:
            The corresponding PatientProfile.
        """
        if patient_id is None:
            patient_id = f"P-{str(uuid.uuid4())[:8].upper()}"

        if patient_id not in self._profiles:
            self._profiles[patient_id] = PatientProfile(patient_id=patient_id)
            logger.info("Created new patient profile: %s", patient_id)

        return self._profiles[patient_id]

    def save_interaction(
        self,
        patient_id: str,
        interaction: Dict[str, Any],
    ) -> None:
        """Save an interaction to a patient's profile.

        Args:
            patient_id: Target patient ID.
            interaction: Dict with query/response data.
        """
        profile = self.get_or_create_profile(patient_id)
        profile.add_interaction(interaction)

    def get_history(
        self,
        patient_id: str,
        n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve a patient's interaction history.

        Args:
            patient_id: Target patient ID.
            n: If provided, return only the last *n* interactions.

        Returns:
            List of interaction dicts.
        """
        profile = self._profiles.get(patient_id)
        if profile is None:
            return []
        if n is not None:
            return profile.get_recent_context(n)
        return profile.interactions

    def list_patients(self) -> List[str]:
        """Return all known patient IDs."""
        return list(self._profiles.keys())

    def patient_count(self) -> int:
        """Return the number of tracked patients."""
        return len(self._profiles)


# Module-level singleton
_global_memory_store: Optional[PatientMemoryStore] = None


def get_memory_store() -> PatientMemoryStore:
    """Return the global PatientMemoryStore singleton."""
    global _global_memory_store
    if _global_memory_store is None:
        _global_memory_store = PatientMemoryStore()
    return _global_memory_store
