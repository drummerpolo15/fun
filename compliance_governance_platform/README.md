# Compliance & Governance Automation Platform

A comprehensive automation platform for data governance, audit preparation, and vendor risk management designed for mid-market companies (200-2,000 employees).

## Overview

This platform addresses three high-opportunity niches in compliance and governance automation:

### 1. Data Governance Automation
Positioned between overbuilt enterprise tools (like Collibra) and underpowered spreadsheets, this module provides:
- **Data Lineage Tracking**: Track upstream and downstream dependencies between data assets
- **Data Ownership Management**: Maintain ownership and stewardship information
- **PII Exposure Tracking**: Identify and track Personally Identifiable Information across your data assets
- **Access Reviews**: Schedule and track periodic access certifications

**Target**: Companies with 200-2,000 employees managing data governance

### 2. SOX / Internal Audit Prep Automation
Streamline audit preparation for finance and audit leaders:
- **Evidence Collection**: Centralized evidence storage and tracking
- **Control Testing**: Schedule, track, and manage control tests with reminders
- **Change Tracking**: Complete audit trail of changes to controls, processes, and systems

**Target**: Finance & audit leaders preparing for SOX audits and internal audits

### 3. Vendor Risk / Security Questionnaire Automation
Automate vendor risk assessments and security questionnaires:
- **Questionnaire Templates**: Pre-built templates for SOC2, ISO27001, HIPAA, and other frameworks
- **Response Management**: Collect and store questionnaire responses
- **Response Reuse Library**: Reuse standard responses across questionnaires
- **Cross-Framework Mapping**: Map responses from one framework (e.g., SOC2) to another (e.g., ISO)

**Target**: Companies managing vendor risk assessments and security questionnaires

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Initialize the database:

```bash
python main.py --init-db
```

This creates a SQLite database file (default: `compliance_governance.db`).

## Usage

### Basic Usage

Show a summary of all metrics:

```bash
python main.py --summary
```

### Configuration

The platform uses a `config.json` file for configuration. If the file doesn't exist, it will be created with default values:

```json
{
  "database": {
    "path": "compliance_governance.db",
    "echo": false
  },
  "notifications": {
    "enabled": false,
    "email": {
      "smtp_server": "",
      "smtp_port": 587,
      "username": "",
      "password": ""
    }
  },
  "reminders": {
    "enabled": true,
    "days_ahead": 7
  },
  "evidence": {
    "storage_path": "evidence/"
  }
}
```

## Architecture

The platform is organized into modular components:

### Core Modules

- **`database.py`**: Database models and schema using SQLAlchemy ORM
- **`config_manager.py`**: Configuration management
- **`main.py`**: Main CLI entry point

### Functional Modules

- **`data_governance.py`**: Data governance automation (lineage, ownership, PII, access reviews)
- **`audit_prep.py`**: SOX/audit prep automation (controls, tests, evidence, change tracking)
- **`vendor_risk.py`**: Vendor risk and questionnaire automation

## Database Schema

The platform uses a SQLite database with the following main entities:

### Data Governance
- `data_assets`: Data assets (tables, files, databases, APIs)
- `data_lineage`: Lineage relationships between assets
- `pii_exposure`: PII fields and their classifications
- `access_reviews`: Access review records

### Audit Prep
- `audit_controls`: Audit controls (SOX, SOC2, ISO, etc.)
- `control_tests`: Control test execution records
- `evidence_records`: Evidence collection records
- `change_tracking`: Change tracking audit trail

### Vendor Risk
- `vendors`: Vendor information
- `questionnaires`: Questionnaire instances
- `questionnaire_templates`: Reusable questionnaire templates
- `questionnaire_responses`: Individual question responses
- `response_reuse`: Response reuse library

## Python API Examples

### Data Governance

```python
from database import init_database, get_session
from data_governance import DataGovernanceManager

# Initialize
engine = init_database("compliance_governance.db")
session = get_session(engine)
dg = DataGovernanceManager(session)

# Create a data asset
asset = dg.create_data_asset(
    name="customers table",
    asset_type="table",
    location="production_db.customers",
    owner_email="data.owner@company.com",
    steward_email="data.steward@company.com"
)

# Track PII exposure
pii = dg.record_pii_exposure(
    asset_id=asset.id,
    field_name="email",
    pii_type="email",
    sensitivity_level="confidential",
    encryption_status="encrypted"
)

# Create lineage relationship
lineage = dg.create_lineage(
    source_asset_id=source_asset.id,
    target_asset_id=target_asset.id,
    transformation_type="ETL",
    transformation_details="Daily ETL job extracts and transforms data"
)

# Get summary
summary = dg.get_governance_summary()
```

### Audit Prep

```python
from database import ComplianceFramework, ReviewStatus
from audit_prep import AuditPrepManager

ap = AuditPrepManager(session)

# Create a control
control = ap.create_control(
    control_id="SOX-001",
    control_name="User Access Reviews",
    control_owner_email="control.owner@company.com",
    framework=ComplianceFramework.SOX,
    frequency="quarterly"
)

# Create a control test
from datetime import datetime, timedelta
test = ap.create_control_test(
    control_id=control.id,
    tester_email="tester@company.com",
    test_period_start=datetime(2024, 1, 1),
    test_period_end=datetime(2024, 3, 31),
    due_date=datetime(2024, 4, 15)
)

# Record evidence
evidence = ap.create_evidence_record(
    control_id=control.id,
    evidence_name="Q1 2024 Access Review Report",
    collected_by="auditor@company.com",
    evidence_type="document",
    file_path="evidence/access_review_q1_2024.pdf"
)

# Track changes
change = ap.track_change(
    entity_type="control",
    entity_id="SOX-001",
    change_type="updated",
    changed_by="admin@company.com",
    change_description="Updated control description"
)
```

### Vendor Risk

```python
from database import ComplianceFramework
from vendor_risk import VendorRiskManager

vr = VendorRiskManager(session)

# Create a vendor
vendor = vr.create_vendor(
    vendor_name="CloudProvider Inc",
    primary_contact_email="vendor@cloudprovider.com"
)

# Create a questionnaire
questionnaire = vr.create_questionnaire(
    vendor_id=vendor.id,
    framework=ComplianceFramework.SOC2,
    created_by="procurement@company.com",
    due_date=datetime(2024, 5, 1)
)

# Create a reusable response
reusable = vr.create_reusable_response(
    question_key="encryption_at_rest",
    standard_response="Yes, we encrypt all data at rest using AES-256 encryption.",
    framework=ComplianceFramework.SOC2
)

# Use reusable response
response_text = vr.use_reusable_response("encryption_at_rest", ComplianceFramework.SOC2)

# Create questionnaire response
response = vr.create_response(
    questionnaire_id=questionnaire.id,
    question_id="Q1",
    question_text="Do you encrypt data at rest?",
    response_value=response_text,
    response_type="yes_no"
)
```

## Data Modeling Approach

The platform follows dimensional modeling principles:

### Dimension Tables
- **Data Assets**: Core dimension (with SCD2 capability for historical ownership)
- **Audit Controls**: Control definitions (with SCD2 for control changes)
- **Vendors**: Vendor information (with SCD2 for vendor changes)
- **Questionnaire Templates**: Reference data

### Fact Tables
- **Data Lineage**: Fact table recording relationships between assets
- **PII Exposure**: Fact table tracking PII fields
- **Access Reviews**: Fact table with time-series (review history)
- **Control Tests**: Fact table with time-series (test execution history)
- **Evidence Records**: Fact table tracking evidence artifacts
- **Change Tracking**: Fact table with time-series (audit trail)
- **Questionnaires**: Fact table tracking questionnaire submissions
- **Questionnaire Responses**: Fact table storing all responses

### Key Design Decisions
- **Time-Series Support**: Access reviews, control tests, and change tracking maintain historical records
- **SCD2 Readiness**: Data assets, controls, and vendors can be extended for SCD2 (effective/expiration dates) if needed
- **Audit Trail**: All changes are tracked through the change_tracking table
- **Flexible Frameworks**: Support for multiple compliance frameworks (SOX, SOC2, ISO27001, HIPAA, GDPR, PCI-DSS)

## Features in Detail

### Data Governance

**Data Lineage**
- Track upstream and downstream dependencies
- Record transformation details (ETL, SQL, APIs)
- Verify lineage relationships

**PII Tracking**
- Identify and classify PII fields
- Track encryption status
- Monitor unencrypted PII (security risk)

**Access Reviews**
- Schedule periodic access certifications
- Track review status
- Identify overdue reviews

### Audit Prep

**Control Testing**
- Schedule control tests based on frequency
- Track test execution and results
- Generate reminders for upcoming tests
- Identify overdue tests

**Evidence Collection**
- Store evidence files and metadata
- Link evidence to controls
- Track evidence collection dates

**Change Tracking**
- Complete audit trail of changes
- Track who changed what and when
- Approval workflow for changes

### Vendor Risk

**Questionnaire Management**
- Create questionnaires from templates
- Track questionnaire status (draft, sent, in_progress, completed)
- Manage due dates and reminders

**Response Reuse**
- Build a library of standard responses
- Reuse responses across questionnaires
- Track response usage

**Framework Mapping**
- Map questions across frameworks (e.g., SOC2 to ISO)
- Reuse responses from one framework in another

## Limitations and Future Enhancements

### Current Limitations
- **SCD2 Implementation**: Current implementation uses simple updates; full SCD2 (with effective/expiration dates) can be added
- **Question Matching**: Response reuse uses simple keyword matching; NLP/ML-based matching would improve accuracy
- **Framework Mapping**: Cross-framework mapping is simplified; a mapping table/config would enable more robust mapping
- **Notifications**: Email notifications are configured but not implemented
- **Evidence Storage**: File path storage is configured but file upload/management not implemented

### Future Enhancements
- [ ] Full SCD2 implementation for dimension tables
- [ ] NLP-based question matching for response reuse
- [ ] Comprehensive framework mapping tables
- [ ] Email notification system
- [ ] Evidence file upload and management
- [ ] Web UI/dashboard
- [ ] API endpoints (REST API)
- [ ] Integration with LDAP/Active Directory for access reviews
- [ ] Automated lineage discovery
- [ ] Integration with data catalogs
- [ ] Reporting and analytics dashboard
- [ ] Export capabilities (PDF reports, Excel exports)

## QA Steps

### Database Integrity
```bash
# Check database exists and is accessible
python -c "from database import init_database, get_session; engine = init_database('compliance_governance.db'); session = get_session(engine); print('Database OK')"
```

### Module Tests
```python
# Test data governance
python -c "from database import init_database, get_session; from data_governance import DataGovernanceManager; engine = init_database('compliance_governance.db'); session = get_session(engine); dg = DataGovernanceManager(session); print(dg.get_governance_summary())"

# Test audit prep
python -c "from database import init_database, get_session; from audit_prep import AuditPrepManager; engine = init_database('compliance_governance.db'); session = get_session(engine); ap = AuditPrepManager(session); print(ap.get_audit_prep_summary())"

# Test vendor risk
python -c "from database import init_database, get_session; from vendor_risk import VendorRiskManager; engine = init_database('compliance_governance.db'); session = get_session(engine); vr = VendorRiskManager(session); print(vr.get_vendor_risk_summary())"
```

### Run Summary
```bash
python main.py --summary
```

## License

This project is provided as-is for educational and personal use.

