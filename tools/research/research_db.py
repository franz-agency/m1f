"""
Database management for m1f-research with dual DB system
"""
import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResearchJob:
    """Research job data model"""
    job_id: str
    query: str
    created_at: datetime
    updated_at: datetime
    status: str  # active, completed, failed
    config: Dict[str, Any]
    output_dir: str
    
    @classmethod
    def create_new(cls, query: str, config: Dict[str, Any], output_dir: str) -> 'ResearchJob':
        """Create a new research job"""
        now = datetime.now()
        return cls(
            job_id=str(uuid.uuid4())[:8],  # Short ID for convenience
            query=query,
            created_at=now,
            updated_at=now,
            status='active',
            config=config,
            output_dir=output_dir
        )


class ResearchDatabase:
    """Main research jobs database manager"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the main research database"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    config TEXT NOT NULL,
                    output_dir TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_stats (
                    job_id TEXT PRIMARY KEY,
                    total_urls INTEGER DEFAULT 0,
                    scraped_urls INTEGER DEFAULT 0,
                    filtered_urls INTEGER DEFAULT 0,
                    analyzed_urls INTEGER DEFAULT 0,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                )
            """)
            
            conn.commit()
    
    def create_job(self, job: ResearchJob) -> str:
        """Create a new research job"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO jobs (job_id, query, created_at, updated_at, status, config, output_dir)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    job.job_id,
                    job.query,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.status,
                    json.dumps(job.config),
                    job.output_dir
                )
            )
            
            # Initialize stats
            conn.execute(
                "INSERT INTO job_stats (job_id) VALUES (?)",
                (job.job_id,)
            )
            
            conn.commit()
        
        logger.info(f"Created new job: {job.job_id} for query: {job.query}")
        return job.job_id
    
    def get_job(self, job_id: str) -> Optional[ResearchJob]:
        """Get a research job by ID"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return ResearchJob(
                    job_id=row['job_id'],
                    query=row['query'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    status=row['status'],
                    config=json.loads(row['config']),
                    output_dir=row['output_dir']
                )
        
        return None
    
    def update_job_status(self, job_id: str, status: str):
        """Update job status"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, datetime.now().isoformat(), job_id)
            )
            conn.commit()
    
    def update_job_stats(self, job_id: str, **stats):
        """Update job statistics"""
        with sqlite3.connect(str(self.db_path)) as conn:
            # Build dynamic update query
            updates = []
            values = []
            for key, value in stats.items():
                if key in ['total_urls', 'scraped_urls', 'filtered_urls', 'analyzed_urls']:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if updates:
                values.append(job_id)
                query = f"UPDATE job_stats SET {', '.join(updates)} WHERE job_id = ?"
                conn.execute(query, values)
                conn.commit()
    
    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all jobs with optional status filter"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT j.*, s.total_urls, s.scraped_urls, s.filtered_urls, s.analyzed_urls
                FROM jobs j
                LEFT JOIN job_stats s ON j.job_id = s.job_id
            """
            params = []
            
            if status:
                query += " WHERE j.status = ?"
                params.append(status)
            
            query += " ORDER BY j.created_at DESC"
            
            cursor = conn.execute(query, params)
            
            jobs = []
            for row in cursor:
                jobs.append({
                    'job_id': row['job_id'],
                    'query': row['query'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'status': row['status'],
                    'output_dir': row['output_dir'],
                    'stats': {
                        'total_urls': row['total_urls'] or 0,
                        'scraped_urls': row['scraped_urls'] or 0,
                        'filtered_urls': row['filtered_urls'] or 0,
                        'analyzed_urls': row['analyzed_urls'] or 0
                    }
                })
            
            return jobs


class JobDatabase:
    """Per-job database for URL and content tracking"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the job-specific database"""
        with sqlite3.connect(str(self.db_path)) as conn:
            # URL tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    url TEXT PRIMARY KEY,
                    normalized_url TEXT,
                    host TEXT,
                    added_by TEXT NOT NULL,
                    added_at TIMESTAMP NOT NULL,
                    scraped_at TIMESTAMP,
                    status_code INTEGER,
                    content_checksum TEXT,
                    error_message TEXT
                )
            """)
            
            # Content storage
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    markdown TEXT NOT NULL,
                    metadata TEXT,
                    word_count INTEGER,
                    filtered BOOLEAN DEFAULT 0,
                    filter_reason TEXT,
                    FOREIGN KEY (url) REFERENCES urls(url)
                )
            """)
            
            # Analysis results
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis (
                    url TEXT PRIMARY KEY,
                    relevance_score REAL,
                    key_points TEXT,
                    content_type TEXT,
                    analysis_data TEXT,
                    analyzed_at TIMESTAMP,
                    FOREIGN KEY (url) REFERENCES urls(url)
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_urls_host ON urls(host)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_urls_scraped ON urls(scraped_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_filtered ON content(filtered)")
            
            conn.commit()
    
    def add_urls(self, urls: List[Dict[str, str]], added_by: str = 'llm') -> int:
        """Add URLs to the database"""
        added_count = 0
        
        with sqlite3.connect(str(self.db_path)) as conn:
            for url_data in urls:
                url = url_data.get('url', '')
                if not url:
                    continue
                
                try:
                    # Normalize URL
                    from urllib.parse import urlparse, urlunparse
                    parsed = urlparse(url)
                    normalized = urlunparse((
                        parsed.scheme.lower(),
                        parsed.netloc.lower(),
                        parsed.path.rstrip('/'),
                        parsed.params,
                        parsed.query,
                        ''
                    ))
                    
                    conn.execute(
                        """INSERT OR IGNORE INTO urls 
                           (url, normalized_url, host, added_by, added_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            url,
                            normalized,
                            parsed.netloc,
                            added_by,
                            datetime.now().isoformat()
                        )
                    )
                    
                    if conn.total_changes > added_count:
                        added_count = conn.total_changes
                        
                except Exception as e:
                    logger.error(f"Error adding URL {url}: {e}")
            
            conn.commit()
        
        return added_count
    
    def get_unscraped_urls(self) -> List[str]:
        """Get all URLs that haven't been scraped yet"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT url FROM urls WHERE scraped_at IS NULL"
            )
            return [row[0] for row in cursor]
    
    def get_urls_by_host(self) -> Dict[str, List[str]]:
        """Get URLs grouped by host"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT host, url FROM urls WHERE scraped_at IS NULL ORDER BY host"
            )
            
            urls_by_host = {}
            for host, url in cursor:
                if host not in urls_by_host:
                    urls_by_host[host] = []
                urls_by_host[host].append(url)
            
            return urls_by_host
    
    def mark_url_scraped(self, url: str, status_code: int, 
                         content_checksum: Optional[str] = None,
                         error_message: Optional[str] = None):
        """Mark a URL as scraped"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """UPDATE urls 
                   SET scraped_at = ?, status_code = ?, 
                       content_checksum = ?, error_message = ?
                   WHERE url = ?""",
                (
                    datetime.now().isoformat(),
                    status_code,
                    content_checksum,
                    error_message,
                    url
                )
            )
            conn.commit()
    
    def save_content(self, url: str, title: str, markdown: str, 
                     metadata: Dict[str, Any], filtered: bool = False,
                     filter_reason: Optional[str] = None):
        """Save scraped content"""
        word_count = len(markdown.split())
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO content 
                   (url, title, markdown, metadata, word_count, filtered, filter_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    url,
                    title,
                    markdown,
                    json.dumps(metadata),
                    word_count,
                    filtered,
                    filter_reason
                )
            )
            conn.commit()
    
    def save_analysis(self, url: str, relevance_score: float,
                      key_points: List[str], content_type: str,
                      analysis_data: Dict[str, Any]):
        """Save content analysis results"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO analysis 
                   (url, relevance_score, key_points, content_type, 
                    analysis_data, analyzed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    url,
                    relevance_score,
                    json.dumps(key_points),
                    content_type,
                    json.dumps(analysis_data),
                    datetime.now().isoformat()
                )
            )
            conn.commit()
    
    def get_content_for_bundle(self) -> List[Dict[str, Any]]:
        """Get all non-filtered content for bundle creation"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT c.*, a.relevance_score, a.key_points, a.content_type
                FROM content c
                LEFT JOIN analysis a ON c.url = a.url
                WHERE c.filtered = 0
                ORDER BY a.relevance_score DESC NULLS LAST
            """)
            
            content = []
            for row in cursor:
                content.append({
                    'url': row['url'],
                    'title': row['title'],
                    'markdown': row['markdown'],
                    'metadata': json.loads(row['metadata']),
                    'word_count': row['word_count'],
                    'relevance_score': row['relevance_score'],
                    'key_points': json.loads(row['key_points']) if row['key_points'] else [],
                    'content_type': row['content_type']
                })
            
            return content
    
    def get_stats(self) -> Dict[str, int]:
        """Get job statistics"""
        with sqlite3.connect(str(self.db_path)) as conn:
            stats = {}
            
            # Total URLs
            cursor = conn.execute("SELECT COUNT(*) FROM urls")
            stats['total_urls'] = cursor.fetchone()[0]
            
            # Scraped URLs
            cursor = conn.execute("SELECT COUNT(*) FROM urls WHERE scraped_at IS NOT NULL")
            stats['scraped_urls'] = cursor.fetchone()[0]
            
            # Filtered URLs
            cursor = conn.execute("SELECT COUNT(*) FROM content WHERE filtered = 1")
            stats['filtered_urls'] = cursor.fetchone()[0]
            
            # Analyzed URLs
            cursor = conn.execute("SELECT COUNT(*) FROM analysis")
            stats['analyzed_urls'] = cursor.fetchone()[0]
            
            return stats