# llm_archive/cli_cursors.py
"""
CLI utilities for cursor management and diagnostics.

Provides commands to view, analyze, and manage annotator cursors
with runtime statistics.
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from llm_archive.annotations.cursor import CursorManager


class CursorStats:
    """
    Utilities for cursor statistics and diagnostics.
    
    Helps identify problematic annotators by analyzing:
    - Cumulative runtime
    - Processing efficiency (entities/second)
    - Annotation yield (annotations/entity)
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.cursor_manager = CursorManager(session)
    
    def show_all_cursors(self, order_by: str = 'runtime') -> None:
        """
        Display all cursors with statistics.
        
        Args:
            order_by: Sort order - 'runtime', 'entities', 'annotations', or 'updated'
        """
        cursors = self.cursor_manager.get_all_cursors()
        
        if not cursors:
            print("No cursors found.")
            return
        
        # Sort cursors
        if order_by == 'runtime':
            cursors.sort(key=lambda c: c.cumulative_runtime_seconds, reverse=True)
        elif order_by == 'entities':
            cursors.sort(key=lambda c: c.entities_processed, reverse=True)
        elif order_by == 'annotations':
            cursors.sort(key=lambda c: c.annotations_created, reverse=True)
        elif order_by == 'updated':
            cursors.sort(key=lambda c: c.updated_at, reverse=True)
        
        # Print header
        print("\n" + "=" * 120)
        print(f"{'Annotator':<40} {'Version':<10} {'Entity Type':<20} {'Runtime':<12} {'Entities':<12} {'Annotations':<12}")
        print("=" * 120)
        
        # Print cursor stats
        for cursor in cursors:
            runtime_str = self._format_runtime(cursor.cumulative_runtime_seconds)
            entities_str = f"{cursor.entities_processed:,}"
            annotations_str = f"{cursor.annotations_created:,}"
            
            print(
                f"{cursor.annotator_name:<40} "
                f"{cursor.annotator_version:<10} "
                f"{cursor.entity_type:<20} "
                f"{runtime_str:<12} "
                f"{entities_str:<12} "
                f"{annotations_str:<12}"
            )
        
        print("=" * 120)
        
        # Print summary
        total_runtime = sum(c.cumulative_runtime_seconds for c in cursors)
        total_entities = sum(c.entities_processed for c in cursors)
        total_annotations = sum(c.annotations_created for c in cursors)
        
        print(f"\nTotal: {len(cursors)} cursors")
        print(f"Total runtime: {self._format_runtime(total_runtime)}")
        print(f"Total entities processed: {total_entities:,}")
        print(f"Total annotations created: {total_annotations:,}")
        print()
    
    def show_detailed_stats(self, annotator_name: Optional[str] = None) -> None:
        """
        Show detailed statistics with efficiency metrics.
        
        Args:
            annotator_name: If specified, only show stats for this annotator
        """
        cursors = self.cursor_manager.get_all_cursors()
        
        if annotator_name:
            cursors = [c for c in cursors if c.annotator_name == annotator_name]
        
        if not cursors:
            print(f"No cursors found{f' for {annotator_name}' if annotator_name else ''}.")
            return
        
        print("\n" + "=" * 140)
        print(
            f"{'Annotator':<40} {'Runtime':<12} {'Entities':<10} {'Ann.':<10} "
            f"{'Ent/sec':<10} {'Ann/ent':<10} {'Last Updated':<25}"
        )
        print("=" * 140)
        
        for cursor in cursors:
            # Calculate efficiency metrics
            entities_per_sec = (
                cursor.entities_processed / cursor.cumulative_runtime_seconds
                if cursor.cumulative_runtime_seconds > 0 else 0
            )
            annotations_per_entity = (
                cursor.annotations_created / cursor.entities_processed
                if cursor.entities_processed > 0 else 0
            )
            
            runtime_str = self._format_runtime(cursor.cumulative_runtime_seconds)
            entities_str = f"{cursor.entities_processed:,}"
            annotations_str = f"{cursor.annotations_created:,}"
            ent_per_sec_str = f"{entities_per_sec:.1f}"
            ann_per_ent_str = f"{annotations_per_entity:.2f}"
            updated_str = cursor.updated_at.strftime('%Y-%m-%d %H:%M:%S %Z')
            
            full_name = f"{cursor.annotator_name} v{cursor.annotator_version} ({cursor.entity_type})"
            
            print(
                f"{full_name:<40} "
                f"{runtime_str:<12} "
                f"{entities_str:<10} "
                f"{annotations_str:<10} "
                f"{ent_per_sec_str:<10} "
                f"{ann_per_ent_str:<10} "
                f"{updated_str:<25}"
            )
        
        print("=" * 140 + "\n")
    
    def identify_slow_annotators(self, threshold_seconds: float = 60.0) -> None:
        """
        Identify annotators with high cumulative runtime.
        
        Args:
            threshold_seconds: Minimum runtime to be considered "slow"
        """
        cursors = self.cursor_manager.get_all_cursors()
        slow_cursors = [
            c for c in cursors 
            if c.cumulative_runtime_seconds >= threshold_seconds
        ]
        
        if not slow_cursors:
            print(f"No annotators with runtime >= {threshold_seconds}s")
            return
        
        # Sort by runtime
        slow_cursors.sort(key=lambda c: c.cumulative_runtime_seconds, reverse=True)
        
        print(f"\n🐌 Annotators with cumulative runtime >= {threshold_seconds}s:\n")
        
        for cursor in slow_cursors:
            runtime_str = self._format_runtime(cursor.cumulative_runtime_seconds)
            
            # Calculate efficiency
            if cursor.cumulative_runtime_seconds > 0:
                ent_per_sec = cursor.entities_processed / cursor.cumulative_runtime_seconds
                seconds_per_ent = cursor.cumulative_runtime_seconds / cursor.entities_processed if cursor.entities_processed > 0 else 0
            else:
                ent_per_sec = 0
                seconds_per_ent = 0
            
            print(f"  • {cursor.annotator_name} v{cursor.annotator_version} ({cursor.entity_type})")
            print(f"    Runtime: {runtime_str}")
            print(f"    Processed: {cursor.entities_processed:,} entities")
            print(f"    Efficiency: {ent_per_sec:.1f} entities/sec ({seconds_per_ent*1000:.1f} ms/entity)")
            print(f"    Created: {cursor.annotations_created:,} annotations")
            print()
    
    def _format_runtime(self, seconds: float) -> str:
        """Format runtime in human-readable form."""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.2f}h"


def print_cursor_stats(
    session: Session,
    order_by: str = 'runtime',
    detailed: bool = False,
    slow_threshold: Optional[float] = None,
) -> None:
    """
    Convenience function to print cursor statistics.
    
    Args:
        session: Database session
        order_by: Sort order for cursor list
        detailed: Show detailed statistics with efficiency metrics
        slow_threshold: If set, identify slow annotators above this threshold
    """
    stats = CursorStats(session)
    
    if slow_threshold is not None:
        stats.identify_slow_annotators(slow_threshold)
    elif detailed:
        stats.show_detailed_stats()
    else:
        stats.show_all_cursors(order_by=order_by)


# Example usage:
if __name__ == '__main__':
    from llm_archive.config import get_session
    
    with get_session() as session:
        # Show all cursors ordered by runtime
        print_cursor_stats(session, order_by='runtime')
        
        # Show detailed stats
        print_cursor_stats(session, detailed=True)
        
        # Identify slow annotators (>60s cumulative runtime)
        print_cursor_stats(session, slow_threshold=60.0)
