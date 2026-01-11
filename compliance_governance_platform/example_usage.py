#!/usr/bin/env python3
"""
Example usage script for the Compliance & Governance Automation Platform.

This script demonstrates how to use the platform's three main modules:
1. Data Governance
2. Audit Prep
3. Vendor Risk
"""

from datetime import datetime, timedelta
from database import (
    init_database, get_session,
    ComplianceFramework, ReviewStatus
)
from data_governance import DataGovernanceManager
from audit_prep import AuditPrepManager
from vendor_risk import VendorRiskManager


def example_data_governance(session):
    """Example: Data Governance operations."""
    print("\n" + "="*70)
    print("DATA GOVERNANCE EXAMPLE")
    print("="*70)
    
    dg = DataGovernanceManager(session)
    
    # Create data assets
    print("\n1. Creating data assets...")
    customers_table = dg.create_data_asset(
        name="customers table",
        asset_type="table",
        location="production_db.customers",
        owner_email="data.owner@company.com",
        steward_email="data.steward@company.com",
        description="Main customers table"
    )
    print(f"   Created asset: {customers_table.name} (ID: {customers_table.id})")
    
    sales_view = dg.create_data_asset(
        name="sales analytics view",
        asset_type="view",
        location="analytics_db.sales_analytics",
        owner_email="analytics.team@company.com"
    )
    print(f"   Created asset: {sales_view.name} (ID: {sales_view.id})")
    
    # Track PII exposure
    print("\n2. Tracking PII exposure...")
    pii_email = dg.record_pii_exposure(
        asset_id=customers_table.id,
        field_name="email",
        pii_type="email",
        sensitivity_level="confidential",
        encryption_status="encrypted",
        reviewed_by="security.team@company.com"
    )
    print(f"   Recorded PII: {pii_email.field_name} ({pii_email.pii_type}) - {pii_email.encryption_status}")
    
    # Create lineage relationship
    print("\n3. Creating lineage relationship...")
    lineage = dg.create_lineage(
        source_asset_id=customers_table.id,
        target_asset_id=sales_view.id,
        transformation_type="ETL",
        transformation_details="Daily ETL job extracts and transforms customer data",
        verified_by="data.engineer@company.com"
    )
    print(f"   Created lineage: {customers_table.name} -> {sales_view.name}")
    
    # Create access review
    print("\n4. Creating access review...")
    review = dg.create_access_review(
        asset_id=customers_table.id,
        reviewer_email="data.owner@company.com",
        review_period_start=datetime(2024, 1, 1),
        review_period_end=datetime(2024, 3, 31),
        due_date=datetime(2024, 4, 15)
    )
    print(f"   Created access review (Due: {review.due_date.date()})")
    
    # Get summary
    print("\n5. Data Governance Summary:")
    summary = dg.get_governance_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")


def example_audit_prep(session):
    """Example: Audit Prep operations."""
    print("\n" + "="*70)
    print("AUDIT PREP EXAMPLE")
    print("="*70)
    
    ap = AuditPrepManager(session)
    
    # Create a control
    print("\n1. Creating audit control...")
    control = ap.create_control(
        control_id="SOX-001",
        control_name="User Access Reviews",
        control_owner_email="control.owner@company.com",
        framework=ComplianceFramework.SOX,
        control_description="Quarterly user access reviews are performed",
        control_type="detective",
        frequency="quarterly"
    )
    print(f"   Created control: {control.control_id} - {control.control_name}")
    
    # Create a control test
    print("\n2. Creating control test...")
    test = ap.create_control_test(
        control_id=control.id,
        tester_email="tester@company.com",
        test_period_start=datetime(2024, 1, 1),
        test_period_end=datetime(2024, 3, 31),
        due_date=datetime(2024, 4, 15)
    )
    print(f"   Created test (Due: {test.due_date.date()})")
    
    # Record evidence
    print("\n3. Recording evidence...")
    evidence = ap.create_evidence_record(
        control_id=control.id,
        evidence_name="Q1 2024 Access Review Report",
        collected_by="auditor@company.com",
        evidence_type="document",
        file_path="evidence/access_review_q1_2024.pdf",
        evidence_period_start=datetime(2024, 1, 1),
        evidence_period_end=datetime(2024, 3, 31),
        description="Quarterly access review report for Q1 2024"
    )
    print(f"   Recorded evidence: {evidence.evidence_name}")
    
    # Track a change
    print("\n4. Tracking change...")
    change = ap.track_change(
        entity_type="control",
        entity_id="SOX-001",
        change_type="updated",
        changed_by="admin@company.com",
        change_description="Updated control description",
        old_values={"description": "Old description"},
        new_values={"description": "New description"}
    )
    print(f"   Tracked change: {change.change_type} to {change.entity_type} {change.entity_id}")
    
    # Get summary
    print("\n5. Audit Prep Summary:")
    summary = ap.get_audit_prep_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")


def example_vendor_risk(session):
    """Example: Vendor Risk operations."""
    print("\n" + "="*70)
    print("VENDOR RISK EXAMPLE")
    print("="*70)
    
    vr = VendorRiskManager(session)
    
    # Create a vendor
    print("\n1. Creating vendor...")
    vendor = vr.create_vendor(
        vendor_name="CloudProvider Inc",
        vendor_email="info@cloudprovider.com",
        vendor_website="https://www.cloudprovider.com",
        vendor_type="SaaS",
        primary_contact_email="vendor@cloudprovider.com",
        description="Cloud infrastructure provider"
    )
    print(f"   Created vendor: {vendor.vendor_name}")
    
    # Create a questionnaire template
    print("\n2. Creating questionnaire template...")
    template_json = {
        "questions": [
            {
                "id": "Q1",
                "text": "Do you encrypt data at rest?",
                "type": "yes_no",
                "required": True
            },
            {
                "id": "Q2",
                "text": "Describe your encryption method",
                "type": "text",
                "required": False
            },
            {
                "id": "Q3",
                "text": "Do you have SOC2 Type II certification?",
                "type": "yes_no",
                "required": True
            }
        ]
    }
    template = vr.create_questionnaire_template(
        template_name="SOC2 Security Questionnaire",
        framework=ComplianceFramework.SOC2,
        template_json=template_json
    )
    print(f"   Created template: {template.template_name} (Framework: {template.framework.value})")
    
    # Create a reusable response
    print("\n3. Creating reusable response...")
    reusable = vr.create_reusable_response(
        question_key="encryption_at_rest",
        standard_response="Yes, we encrypt all data at rest using AES-256 encryption.",
        framework=ComplianceFramework.SOC2,
        applicable_context="Standard response for encryption questions"
    )
    print(f"   Created reusable response: {reusable.question_key}")
    
    # Create a questionnaire
    print("\n4. Creating questionnaire...")
    questionnaire = vr.create_questionnaire(
        vendor_id=vendor.id,
        framework=ComplianceFramework.SOC2,
        created_by="procurement@company.com",
        questionnaire_type="security",
        due_date=datetime(2024, 5, 1)
    )
    print(f"   Created questionnaire (Due: {questionnaire.due_date.date()})")
    
    # Use reusable response and create questionnaire responses
    print("\n5. Creating questionnaire responses (using reusable response)...")
    response_text = vr.use_reusable_response("encryption_at_rest", ComplianceFramework.SOC2)
    response1 = vr.create_response(
        questionnaire_id=questionnaire.id,
        question_id="Q1",
        question_text="Do you encrypt data at rest?",
        response_value=response_text,
        response_type="yes_no"
    )
    print(f"   Created response: {response1.question_text[:50]}...")
    
    response2 = vr.create_response(
        questionnaire_id=questionnaire.id,
        question_id="Q3",
        question_text="Do you have SOC2 Type II certification?",
        response_value="Yes, we have SOC2 Type II certification valid until 2025-12-31",
        response_type="yes_no"
    )
    print(f"   Created response: {response2.question_text[:50]}...")
    
    # Get summary
    print("\n6. Vendor Risk Summary:")
    summary = vr.get_vendor_risk_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("COMPLIANCE & GOVERNANCE AUTOMATION PLATFORM - EXAMPLES")
    print("="*70)
    
    # Initialize database
    print("\nInitializing database...")
    engine = init_database("compliance_governance.db")
    session = get_session(engine)
    
    try:
        # Run examples
        example_data_governance(session)
        example_audit_prep(session)
        example_vendor_risk(session)
        
        print("\n" + "="*70)
        print("EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nYou can now run: python main.py --summary")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()

