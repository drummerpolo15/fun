#!/usr/bin/env python3
"""
Compliance & Governance Automation Platform

Main entry point for the Compliance & Governance Automation Platform.

This platform provides three main capabilities:
1. Data Governance Automation (lineage, ownership, PII exposure, access reviews)
2. SOX / Internal Audit Prep (evidence collection, control testing, change tracking)
3. Vendor Risk / Security Questionnaire Automation (SOC2, ISO, HIPAA mapping, response reuse)

Target: Mid-market companies (200-2,000 employees)
"""

import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import database and managers
from database import init_database, get_session, ComplianceFramework, ReviewStatus
from config_manager import ConfigManager
from data_governance import DataGovernanceManager
from audit_prep import AuditPrepManager
from vendor_risk import VendorRiskManager


class ComplianceGovernancePlatform:
    """
    Main platform class that orchestrates all three modules.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the platform.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        # Initialize database
        db_path = self.config_manager.get("database.path", "compliance_governance.db")
        self.engine = init_database(db_path)
        self.session = get_session(self.engine)
        
        # Initialize managers
        self.data_governance = DataGovernanceManager(self.session)
        self.audit_prep = AuditPrepManager(self.session)
        self.vendor_risk = VendorRiskManager(self.session)
    
    def close(self):
        """Close database session."""
        self.session.close()
    
    def get_summary(self) -> dict:
        """
        Get a summary of all platform metrics.
        
        Returns:
            Dictionary with summary statistics from all modules
        """
        return {
            'data_governance': self.data_governance.get_governance_summary(),
            'audit_prep': self.audit_prep.get_audit_prep_summary(),
            'vendor_risk': self.vendor_risk.get_vendor_risk_summary()
        }
    
    def print_summary(self):
        """Print a formatted summary of all metrics."""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("COMPLIANCE & GOVERNANCE PLATFORM SUMMARY")
        print("="*70)
        
        # Data Governance Summary
        print("\n📊 DATA GOVERNANCE")
        print("-" * 70)
        dg = summary['data_governance']
        print(f"  Total Assets: {dg['total_assets']}")
        print(f"  Assets Without Owner: {dg['assets_without_owner']}")
        print(f"  Lineage Relationships: {dg['total_lineage_relationships']}")
        print(f"  PII Fields: {dg['total_pii_fields']} (Unencrypted: {dg['unencrypted_pii_fields']})")
        print(f"  Pending Access Reviews: {dg['pending_access_reviews']}")
        print(f"  Overdue Access Reviews: {dg['overdue_access_reviews']}")
        
        # Audit Prep Summary
        print("\n🔍 AUDIT PREP")
        print("-" * 70)
        ap = summary['audit_prep']
        print(f"  Total Controls: {ap['total_controls']}")
        print(f"  Pending Control Tests: {ap['pending_control_tests']}")
        print(f"  Overdue Control Tests: {ap['overdue_control_tests']}")
        print(f"  Evidence Records: {ap['total_evidence_records']}")
        print(f"  Pending Change Approvals: {ap['pending_change_approvals']}")
        
        # Vendor Risk Summary
        print("\n🏢 VENDOR RISK")
        print("-" * 70)
        vr = summary['vendor_risk']
        print(f"  Total Vendors: {vr['total_vendors']}")
        print(f"  Total Questionnaires: {vr['total_questionnaires']}")
        print(f"  Pending Questionnaires: {vr['pending_questionnaires']}")
        print(f"  Overdue Questionnaires: {vr['overdue_questionnaires']}")
        print(f"  Questionnaire Templates: {vr['total_templates']}")
        print(f"  Reusable Responses: {vr['total_reusable_responses']}")
        
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Compliance & Governance Automation Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show summary
  python main.py --summary
  
  # Initialize database
  python main.py --init-db
        """
    )
    
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary of all metrics'
    )
    
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database (creates tables)'
    )
    
    args = parser.parse_args()
    
    # Initialize platform
    platform = ComplianceGovernancePlatform(args.config)
    
    try:
        if args.init_db:
            print("Database initialized successfully!")
            print(f"Database location: {platform.config_manager.get('database.path')}")
            return
        
        if args.summary:
            platform.print_summary()
            return
        
        # Default: show summary
        platform.print_summary()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        platform.close()


if __name__ == "__main__":
    main()

