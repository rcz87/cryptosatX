#!/usr/bin/env python3
"""
Automated script to replace print() statements with structured logger calls
Preserves emoji-based messages and determines appropriate log level
"""

import re
import os
import sys
import logging
from pathlib import Path

# Configure logging for this tool
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def determine_log_level(message: str) -> str:
    """
    Determine appropriate log level based on message content
    
    Returns: 'error', 'warning', or 'info'
    """
    # Error indicators
    if any(keyword in message.lower() for keyword in ['error', 'failed', 'exception', '❌', 'fail']):
        return 'error'
    
    # Warning indicators  
    if any(keyword in message.lower() for keyword in ['warning', 'warn', '⚠️', 'caution', 'deprecated']):
        return 'warning'
    
    # Default to info
    return 'info'


def add_logger_import(content: str, module_name: str) -> str:
    """Add logger import if not already present"""
    if 'from app.utils.logger import get_logger' in content:
        return content
    
    # Find appropriate location (after other imports)
    import_pattern = r'(import .*?\n(?:from .*? import .*?\n)*)'
    
    logger_import = f'\nfrom app.utils.logger import get_logger\n\n# Initialize module logger\nlogger = get_logger(__name__)\n'
    
    # Insert after last import
    match = re.search(import_pattern, content)
    if match:
        insert_pos = match.end()
        return content[:insert_pos] + logger_import + content[insert_pos:]
    else:
        # Insert at beginning if no imports found
        return logger_import + '\n' + content


def replace_print_statements(content: str) -> tuple[str, int]:
    """
    Replace print() statements with appropriate logger calls
    
    Returns: (modified_content, replacement_count)
    """
    replacements = 0
    
    # Pattern to match print statements
    # Handles: print("msg"), print(f"msg"), print("line1\nline2")
    print_pattern = r'print\s*\((.*?)\)'
    
    def replace_print(match):
        nonlocal replacements
        arg = match.group(1).strip()
        
        # Determine log level from message
        log_level = determine_log_level(arg)
        
        replacements += 1
        return f'logger.{log_level}({arg})'
    
    modified_content = re.sub(print_pattern, replace_print, content, flags=re.DOTALL)
    
    return modified_content, replacements


def migrate_file(filepath: Path, dry_run: bool = False) -> dict:
    """
    Migrate a single file from print() to logger calls
    
    Returns: dict with migration stats
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        original_content = content
        
        # Add logger import if needed
        content = add_logger_import(content, filepath.stem)
        
        # Replace print statements
        content, replacements = replace_print_statements(content)
        
        if replacements > 0 and not dry_run:
            filepath.write_text(content, encoding='utf-8')
        
        return {
            'filepath': str(filepath),
            'replacements': replacements,
            'success': True,
            'dry_run': dry_run
        }
    except Exception as e:
        return {
            'filepath': str(filepath),
            'replacements': 0,
            'success': False,
            'error': str(e)
        }


def main():
    """Main migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate print() to logger calls')
    parser.add_argument('paths', nargs='+', help='Files or directories to migrate')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--exclude', nargs='*', default=[], help='Patterns to exclude')
    
    args = parser.parse_args()
    
    # Collect files to process
    files_to_process = []
    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file():
            if path.suffix == '.py':
                files_to_process.append(path)
        elif path.is_dir():
            files_to_process.extend(path.rglob('*.py'))
    
    # Filter excluded patterns
    excluded_patterns = args.exclude + ['__pycache__', 'venv', '.git', 'alembic/versions']
    files_to_process = [
        f for f in files_to_process 
        if not any(pattern in str(f) for pattern in excluded_patterns)
    ]
    
    logger.info(f"{'DRY RUN - ' if args.dry_run else ''}Processing {len(files_to_process)} files...")
    logger.info("")
    
    total_replacements = 0
    success_count = 0
    
    for filepath in sorted(files_to_process):
        result = migrate_file(filepath, dry_run=args.dry_run)
        
        if result['replacements'] > 0:
            status = '✓' if result['success'] else '✗'
            mode = '[DRY RUN] ' if result['dry_run'] else ''
            logger.info(f"{status} {mode}{result['filepath']}: {result['replacements']} replacements")
            total_replacements += result['replacements']
            if result['success']:
                success_count += 1
    
    logger.info("")
    logger.info(f"{'[DRY RUN] ' if args.dry_run else ''}Total: {total_replacements} print() statements replaced in {success_count} files")
    
    if args.dry_run:
        logger.info("\nRun without --dry-run to apply changes")


if __name__ == '__main__':
    main()
