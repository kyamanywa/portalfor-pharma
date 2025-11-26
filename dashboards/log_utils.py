"""
Log Utilities for Django Web-based Log Viewing
Industry standard approach for small-medium Django applications
"""

import os
import re
from datetime import datetime, timedelta
from django.conf import settings
from django.core.paginator import Paginator
from collections import defaultdict

class LogAnalyzer:
    """
    Industry standard log analysis utilities
    Similar to what's used in production Django applications
    """
    
    LOG_LEVELS = {
        'DEBUG': 'secondary',
        'INFO': 'primary', 
        'WARNING': 'warning',
        'ERROR': 'danger',
        'CRITICAL': 'danger'
    }
    
    def __init__(self, log_file_path=None):
        self.log_file_path = log_file_path or os.path.join(settings.BASE_DIR, 'logs', 'django.log')
    
    def get_log_entries(self, limit=100, level_filter=None, date_filter=None, search_query=None):
        """
        Parse log entries with filtering - industry standard approach
        """
        entries = []
        
        if not os.path.exists(self.log_file_path):
            return entries
            
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Parse log entries (Django log format)
            for line in reversed(lines[-limit*2:]):  # Get more than needed for filtering
                entry = self._parse_log_line(line.strip())
                if entry:
                    # Apply filters
                    if level_filter and entry['level'] != level_filter:
                        continue
                    if date_filter and not self._date_matches(entry['timestamp'], date_filter):
                        continue
                    if search_query and search_query.lower() not in entry['message'].lower():
                        continue
                        
                    entries.append(entry)
                    
                    if len(entries) >= limit:
                        break
                        
        except Exception as e:
            entries.append({
                'timestamp': datetime.now(),
                'level': 'ERROR',
                'message': f'Error reading log file: {str(e)}',
                'module': 'log_analyzer',
                'badge_class': 'danger'
            })
            
        return entries
    
    def _parse_log_line(self, line):
        """
        Parse Django log format: LEVEL YYYY-MM-DD HH:MM:SS,mmm module thread_id message
        """
        # Django log pattern
        pattern = r'(\w+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(.*)'
        match = re.match(pattern, line)
        
        if match:
            level, timestamp_str, module, process_id, thread_id, message = match.groups()
            
            try:
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str.split(',')[0], '%Y-%m-%d %H:%M:%S')
                
                return {
                    'timestamp': timestamp,
                    'level': level,
                    'module': module,
                    'process_id': process_id,
                    'thread_id': thread_id,
                    'message': message,
                    'badge_class': self.LOG_LEVELS.get(level, 'secondary'),
                    'raw_line': line
                }
            except ValueError:
                pass
                
        return None
    
    def _date_matches(self, timestamp, date_filter):
        """Check if timestamp matches date filter"""
        if date_filter == 'today':
            return timestamp.date() == datetime.now().date()
        elif date_filter == 'yesterday':
            yesterday = datetime.now().date() - timedelta(days=1)
            return timestamp.date() == yesterday
        elif date_filter == 'week':
            week_ago = datetime.now() - timedelta(days=7)
            return timestamp >= week_ago
        elif date_filter == 'month':
            month_ago = datetime.now() - timedelta(days=30)
            return timestamp >= month_ago
        return True
    
    def get_log_stats(self):
        """
        Get log statistics - common in production monitoring
        """
        entries = self.get_log_entries(limit=1000)
        
        stats = {
            'total_entries': len(entries),
            'level_counts': defaultdict(int),
            'recent_errors': [],
            'top_modules': defaultdict(int),
            'entries_by_hour': defaultdict(int)
        }
        
        for entry in entries:
            stats['level_counts'][entry['level']] += 1
            stats['top_modules'][entry['module']] += 1
            
            # Track recent errors
            if entry['level'] in ['ERROR', 'CRITICAL']:
                stats['recent_errors'].append(entry)
                
            # Entries by hour for activity tracking
            hour_key = entry['timestamp'].strftime('%Y-%m-%d %H:00')
            stats['entries_by_hour'][hour_key] += 1
        
        # Limit recent errors to last 10
        stats['recent_errors'] = stats['recent_errors'][:10]
        
        return stats
    
    def get_log_file_info(self):
        """Get log file information"""
        if os.path.exists(self.log_file_path):
            stat = os.stat(self.log_file_path)
            return {
                'exists': True,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'path': self.log_file_path
            }
        return {'exists': False, 'path': self.log_file_path}


class LogRotationManager:
    """
    Industry standard log rotation management
    """
    
    @staticmethod
    def should_rotate_log(log_path, max_size_mb=50):
        """Check if log should be rotated based on size"""
        if os.path.exists(log_path):
            size_mb = os.path.getsize(log_path) / (1024 * 1024)
            return size_mb > max_size_mb
        return False
    
    @staticmethod
    def rotate_log(log_path, keep_backups=5):
        """
        Rotate log file - industry standard approach
        """
        if not os.path.exists(log_path):
            return False
            
        base_path = log_path.rsplit('.', 1)[0]
        extension = log_path.rsplit('.', 1)[1] if '.' in log_path else 'log'
        
        # Rotate existing backups
        for i in range(keep_backups - 1, 0, -1):
            old_backup = f"{base_path}.{i}.{extension}"
            new_backup = f"{base_path}.{i + 1}.{extension}"
            
            if os.path.exists(old_backup):
                if i == keep_backups - 1:
                    os.remove(old_backup)  # Remove oldest
                else:
                    os.rename(old_backup, new_backup)
        
        # Move current log to .1 backup
        backup_path = f"{base_path}.1.{extension}"
        os.rename(log_path, backup_path)
        
        return True