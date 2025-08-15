# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Workflow phase definitions and management for m1f-research
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """Defines the phases of the research workflow"""

    INITIALIZATION = "initialization"
    QUERY_EXPANSION = "query_expansion"
    URL_COLLECTION = "url_collection"
    URL_REVIEW = "url_review"
    CRAWLING = "crawling"
    BUNDLING = "bundling"
    ANALYSIS = "analysis"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def get_next_phase(
        cls, current_phase: "WorkflowPhase"
    ) -> Optional["WorkflowPhase"]:
        """Get the next phase in the workflow"""
        phase_order = [
            cls.INITIALIZATION,
            cls.QUERY_EXPANSION,
            cls.URL_COLLECTION,
            cls.URL_REVIEW,
            cls.CRAWLING,
            cls.BUNDLING,
            cls.ANALYSIS,
            cls.COMPLETED,
        ]

        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            logger.warning(f"Unknown phase: {current_phase}")

        return None

    @classmethod
    def can_resume_from(cls, phase: "WorkflowPhase") -> bool:
        """Check if a phase can be resumed from"""
        # Can't resume from completed or failed states
        return phase not in [cls.COMPLETED, cls.FAILED]


@dataclass
class PhaseContext:
    """Context data for a workflow phase"""

    phase: WorkflowPhase
    data: Dict[str, Any]
    completed: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "phase": self.phase.value,
            "data": self.data,
            "completed": self.completed,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseContext":
        """Create from dictionary"""
        return cls(
            phase=WorkflowPhase(data["phase"]),
            data=data.get("data", {}),
            completed=data.get("completed", False),
            error=data.get("error"),
        )


class WorkflowManager:
    """Manages workflow phases and transitions"""

    def __init__(self, job_manager=None, config=None):
        """
        Initialize workflow manager

        Args:
            job_manager: JobManager instance for persistence
            config: Research configuration
        """
        self.job_manager = job_manager
        self.config = config
        self.current_phase: Optional[WorkflowPhase] = None
        self.phase_data: Dict[str, Any] = {}

    def set_phase(
        self, job_id: str, phase: WorkflowPhase, data: Optional[Dict[str, Any]] = None
    ):
        """
        Set the current workflow phase

        Args:
            job_id: Job ID
            phase: New phase
            data: Optional phase-specific data
        """
        self.current_phase = phase
        if data:
            self.phase_data = data

        # Persist to database if job_manager available
        if self.job_manager and hasattr(self.job_manager.main_db, "update_job_phase"):
            self.job_manager.main_db.update_job_phase(job_id, phase.value, data)

        logger.info(f"Workflow phase set to: {phase.value}")

    def get_phase(self, job_id: str) -> Optional[PhaseContext]:
        """
        Get current phase context for a job

        Args:
            job_id: Job ID

        Returns:
            PhaseContext or None
        """
        if not self.job_manager:
            return None

        job = self.job_manager.get_job(job_id)
        if not job:
            return None

        # Get phase from job data
        phase_str = getattr(job, "phase", "initialization")
        phase_data = getattr(job, "phase_data", {})

        try:
            phase = WorkflowPhase(phase_str)
            return PhaseContext(phase=phase, data=phase_data)
        except ValueError:
            logger.error(f"Invalid phase in job: {phase_str}")
            return None

    def can_transition_to(
        self, from_phase: WorkflowPhase, to_phase: WorkflowPhase
    ) -> bool:
        """
        Check if transition between phases is valid

        Args:
            from_phase: Current phase
            to_phase: Target phase

        Returns:
            True if transition is valid
        """
        # Can always transition to FAILED
        if to_phase == WorkflowPhase.FAILED:
            return True

        # Check if it's the natural next phase
        next_phase = WorkflowPhase.get_next_phase(from_phase)
        if next_phase == to_phase:
            return True

        # Allow skipping certain phases based on config
        if self.config:
            # Can skip query expansion if disabled
            if (
                from_phase == WorkflowPhase.INITIALIZATION
                and to_phase == WorkflowPhase.URL_COLLECTION
                and not getattr(self.config.workflow, "expand_queries", True)
            ):
                return True

            # Can skip URL review if disabled
            if (
                from_phase == WorkflowPhase.URL_COLLECTION
                and to_phase == WorkflowPhase.CRAWLING
                and getattr(self.config.workflow, "skip_review", False)
            ):
                return True

            # Can skip analysis if disabled
            if (
                from_phase == WorkflowPhase.BUNDLING
                and to_phase == WorkflowPhase.COMPLETED
                and not getattr(self.config.workflow, "generate_analysis", True)
            ):
                return True

        return False

    def transition_to(
        self,
        job_id: str,
        new_phase: WorkflowPhase,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Transition to a new phase if valid

        Args:
            job_id: Job ID
            new_phase: Target phase
            data: Optional phase data

        Returns:
            True if transition successful
        """
        current_context = self.get_phase(job_id)

        if not current_context:
            # No current phase, allow initialization
            if new_phase == WorkflowPhase.INITIALIZATION:
                self.set_phase(job_id, new_phase, data)
                return True
            return False

        if self.can_transition_to(current_context.phase, new_phase):
            self.set_phase(job_id, new_phase, data)
            return True

        logger.warning(
            f"Invalid phase transition: {current_context.phase.value} -> {new_phase.value}"
        )
        return False

    def mark_phase_complete(
        self, job_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark current phase as complete and transition to next

        Args:
            job_id: Job ID
            data: Optional completion data

        Returns:
            True if successful
        """
        current_context = self.get_phase(job_id)

        if not current_context:
            logger.error("No current phase to mark complete")
            return False

        # Mark current phase complete
        current_context.completed = True
        if data:
            current_context.data.update(data)

        # Persist completion
        self.set_phase(job_id, current_context.phase, current_context.data)

        # Determine next phase
        next_phase = self.get_next_phase_with_config(current_context.phase)

        if next_phase:
            return self.transition_to(job_id, next_phase)

        return True

    def get_next_phase_with_config(
        self, current_phase: WorkflowPhase
    ) -> Optional[WorkflowPhase]:
        """
        Get next phase considering configuration

        Args:
            current_phase: Current phase

        Returns:
            Next phase or None
        """
        if not self.config:
            return WorkflowPhase.get_next_phase(current_phase)

        # Handle phase skipping based on config
        next_phase = WorkflowPhase.get_next_phase(current_phase)

        while next_phase:
            # Skip query expansion if disabled
            if next_phase == WorkflowPhase.QUERY_EXPANSION and not getattr(
                self.config.workflow, "expand_queries", True
            ):
                next_phase = WorkflowPhase.get_next_phase(next_phase)
                continue

            # Skip URL review if disabled
            if next_phase == WorkflowPhase.URL_REVIEW and getattr(
                self.config.workflow, "skip_review", False
            ):
                next_phase = WorkflowPhase.get_next_phase(next_phase)
                continue

            # Skip analysis if disabled
            if next_phase == WorkflowPhase.ANALYSIS and not getattr(
                self.config.workflow, "generate_analysis", True
            ):
                next_phase = WorkflowPhase.get_next_phase(next_phase)
                continue

            return next_phase

        return None

    def get_resumable_phase(self, job_id: str) -> Optional[WorkflowPhase]:
        """
        Get the phase to resume from for a job

        Args:
            job_id: Job ID

        Returns:
            Phase to resume from or None
        """
        context = self.get_phase(job_id)

        if not context:
            return WorkflowPhase.INITIALIZATION

        # If current phase is not complete, resume from there
        if not context.completed and WorkflowPhase.can_resume_from(context.phase):
            return context.phase

        # Otherwise, resume from next phase
        next_phase = self.get_next_phase_with_config(context.phase)

        if next_phase and WorkflowPhase.can_resume_from(next_phase):
            return next_phase

        return None

    def get_phase_summary(self, job_id: str) -> Dict[str, Any]:
        """
        Get summary of all phases for a job

        Args:
            job_id: Job ID

        Returns:
            Dictionary with phase information
        """
        context = self.get_phase(job_id)

        if not context:
            return {
                "current_phase": None,
                "completed_phases": [],
                "next_phase": WorkflowPhase.INITIALIZATION.value,
                "can_resume": True,
            }

        # Determine completed phases
        completed_phases = []
        phase_order = [
            WorkflowPhase.INITIALIZATION,
            WorkflowPhase.QUERY_EXPANSION,
            WorkflowPhase.URL_COLLECTION,
            WorkflowPhase.URL_REVIEW,
            WorkflowPhase.CRAWLING,
            WorkflowPhase.BUNDLING,
            WorkflowPhase.ANALYSIS,
        ]

        for phase in phase_order:
            if phase == context.phase:
                if context.completed:
                    completed_phases.append(phase.value)
                break
            completed_phases.append(phase.value)

        next_phase = self.get_next_phase_with_config(context.phase)

        return {
            "current_phase": context.phase.value,
            "completed_phases": completed_phases,
            "next_phase": next_phase.value if next_phase else None,
            "can_resume": WorkflowPhase.can_resume_from(context.phase),
            "phase_data": context.data,
            "error": context.error,
        }
