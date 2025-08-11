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
Job management for m1f-research with persistence and resume support
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..m1f.file_operations import (
    safe_exists,
    safe_mkdir,
)

from .research_db import ResearchDatabase, JobDatabase, ResearchJob
from .config import ResearchConfig

logger = logging.getLogger(__name__)


class JobManager:
    """Manages research jobs with persistence"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        # Note: We'll need to call async init separately
        # For now, keep sync behavior for compatibility

        # Main research database
        self.main_db = ResearchDatabase(self.base_dir / "research_jobs.db")

    def create_job(self, query: str, config: ResearchConfig) -> ResearchJob:
        """Create a new research job"""
        # Create output directory with hierarchical structure
        now = datetime.now()
        output_dir = self.base_dir / now.strftime("%Y/%m/%d")

        # Create job with serializable config
        config_dict = self._serialize_config(config)
        job = ResearchJob.create_new(
            query=query, config=config_dict, output_dir=str(output_dir)
        )

        # Update output directory to include job ID
        job.output_dir = str(
            output_dir / f"{job.job_id}_{self._sanitize_query(query)[:30]}"
        )

        # Save to database
        self.main_db.create_job(job)

        # Create job directory
        job_path = Path(job.output_dir)
        # Note: We'll need to call safe_mkdir separately for full async support
        job_path.mkdir(parents=True, exist_ok=True)

        # Create job-specific database
        job_db = JobDatabase(job_path / "research.db")

        logger.info(f"Created job {job.job_id}: {query}")
        logger.info(f"Output directory: {job.output_dir}")

        return job

    def get_job(self, job_id: str) -> Optional[ResearchJob]:
        """Get an existing job by ID"""
        job = self.main_db.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
        return job

    def get_job_database(self, job: ResearchJob) -> JobDatabase:
        """Get the database for a specific job"""
        job_path = Path(job.output_dir)
        return JobDatabase(job_path / "research.db")

    def update_job_status(self, job_id: str, status: str):
        """Update job status"""
        self.main_db.update_job_status(job_id, status)
        logger.info(f"Updated job {job_id} status to: {status}")

    def update_job_stats(self, job: ResearchJob, **additional_stats):
        """Update job statistics from job database"""
        job_db = self.get_job_database(job)
        stats = job_db.get_stats()
        stats.update(additional_stats)
        self.main_db.update_job_stats(job.job_id, **stats)

    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        date_filter: Optional[str] = None,
        search_term: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List jobs with advanced filtering"""
        return self.main_db.list_jobs(status, limit, offset, date_filter, search_term)

    def count_jobs(
        self,
        status: Optional[str] = None,
        date_filter: Optional[str] = None,
        search_term: Optional[str] = None,
    ) -> int:
        """Count jobs matching filters"""
        return self.main_db.count_jobs(status, date_filter, search_term)

    def find_recent_job(self, query: str) -> Optional[ResearchJob]:
        """Find the most recent job for a similar query"""
        jobs = self.list_jobs(status="active")

        # Simple similarity check (can be improved)
        query_lower = query.lower()
        for job_data in jobs:
            if query_lower in job_data["query"].lower():
                return self.get_job(job_data["job_id"])

        return None

    async def create_symlink_to_latest(self, job: ResearchJob):
        """Create a symlink to the latest research bundle"""
        job_path = Path(job.output_dir)
        bundle_path = job_path / "📚_RESEARCH_BUNDLE.md"

        if safe_exists(bundle_path):
            # Create symlink in base directory
            latest_link = self.base_dir / "latest_research.md"

            # Remove old symlink if exists
            if safe_exists(latest_link) or latest_link.is_symlink():
                latest_link.unlink()

            # Create relative symlink
            try:
                relative_path = Path("..") / bundle_path.relative_to(
                    self.base_dir.parent
                )
                latest_link.symlink_to(relative_path)
                logger.info(f"Created symlink: {latest_link} -> {relative_path}")
            except Exception as e:
                logger.warning(f"Could not create symlink: {e}")
                # Fallback: create absolute symlink
                try:
                    latest_link.symlink_to(bundle_path.absolute())
                except Exception as e2:
                    logger.error(f"Failed to create symlink: {e2}")

    def _sanitize_query(self, query: str) -> str:
        """Sanitize query for directory name"""
        safe_name = "".join(c if c.isalnum() or c in "- " else "_" for c in query)
        return safe_name.replace(" ", "-").lower()

    def get_job_info(self, job: ResearchJob) -> Dict[str, Any]:
        """Get comprehensive job information"""
        job_db = self.get_job_database(job)
        stats = job_db.get_stats()

        bundle_exists = safe_exists(Path(job.output_dir) / "📚_RESEARCH_BUNDLE.md")

        return {
            "job_id": job.job_id,
            "query": job.query,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "output_dir": job.output_dir,
            "stats": stats,
            "bundle_exists": bundle_exists,
        }

    def cleanup_old_jobs(self, days: int = 30):
        """Clean up jobs older than specified days"""
        # TODO: Implement cleanup logic
        pass

    async def cleanup_job_raw_data(self, job_id: str) -> Dict[str, Any]:
        """
        Clean up raw data for a specific job while preserving aggregated data

        Returns:
            Dict with cleanup statistics
        """
        job = self.get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}

        job_db = self.get_job_database(job)
        cleanup_stats = job_db.cleanup_raw_content()

        # Also clean up any HTML files in the job directory
        job_dir = Path(job.output_dir)
        html_files_deleted = 0
        space_freed = 0

        if safe_exists(job_dir):
            # Look for HTML files (if any were saved)
            for html_file in job_dir.glob("**/*.html"):
                try:
                    file_size = html_file.stat().st_size
                    html_file.unlink()
                    html_files_deleted += 1
                    space_freed += file_size
                except Exception as e:
                    logger.error(f"Error deleting {html_file}: {e}")

        cleanup_stats["html_files_deleted"] = html_files_deleted
        cleanup_stats["space_freed_mb"] = round(space_freed / (1024 * 1024), 2)

        logger.info(f"Cleaned up job {job_id}: {cleanup_stats}")
        return cleanup_stats

    async def cleanup_all_raw_data(self) -> Dict[str, Any]:
        """Clean up raw data for all jobs"""
        all_jobs = self.list_jobs()
        total_stats = {
            "jobs_cleaned": 0,
            "files_deleted": 0,
            "space_freed_mb": 0,
            "errors": [],
        }

        for job_info in all_jobs:
            try:
                stats = await self.cleanup_job_raw_data(job_info["job_id"])
                if "error" not in stats:
                    total_stats["jobs_cleaned"] += 1
                    total_stats["files_deleted"] += stats.get("html_files_deleted", 0)
                    total_stats["space_freed_mb"] += stats.get("space_freed_mb", 0)
                else:
                    total_stats["errors"].append(stats["error"])
            except Exception as e:
                total_stats["errors"].append(
                    f"Error cleaning job {job_info['job_id']}: {e}"
                )

        return total_stats

    def _serialize_config(self, config: ResearchConfig) -> Dict[str, Any]:
        """Convert ResearchConfig to serializable dict"""

        def serialize_value(val):
            if hasattr(val, "__dict__"):
                return {k: serialize_value(v) for k, v in val.__dict__.items()}
            elif isinstance(val, Path):
                return str(val)
            elif isinstance(val, (list, tuple)):
                return [serialize_value(v) for v in val]
            elif isinstance(val, dict):
                return {k: serialize_value(v) for k, v in val.items()}
            else:
                return val

        return serialize_value(config)
