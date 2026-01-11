"""
Database models and initialization for the Compliance & Governance Automation Platform.

This module defines the database schema using SQLAlchemy ORM.
The schema supports three main functional areas:
1. Data Governance (lineage, ownership, PII exposure, access reviews)
2. SOX/Audit Prep (evidence collection, control testing, change tracking)
3. Vendor Risk (questionnaire automation, compliance mapping)
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Float, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

Base = declarative_base()


class ReviewStatus(enum.Enum):
    """Status enumeration for access reviews and control tests."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    OVERDUE = "overdue"


class ComplianceFramework(enum.Enum):
    """Supported compliance frameworks."""
    SOX = "sox"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"


# ============================================================================
# DATA GOVERNANCE MODELS
# ============================================================================

class DataAsset(Base):
    """
    Core data asset entity (tables, files, databases, APIs).
    
    Grain: One row per data asset
    Type: Dimension table (SCD2 - track historical ownership changes)
    """
    __tablename__ = 'data_assets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(100), nullable=False)  # table, file, database, api
    location = Column(String(500))  # database name, file path, API endpoint
    description = Column(Text)
    owner_email = Column(String(255))  # Current owner
    steward_email = Column(String(255))  # Data steward
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    lineage_as_source = relationship("DataLineage", foreign_keys="DataLineage.source_asset_id", back_populates="source_asset", cascade="all, delete-orphan")
    lineage_as_target = relationship("DataLineage", foreign_keys="DataLineage.target_asset_id", back_populates="target_asset", cascade="all, delete-orphan")
    pii_records = relationship("PIIExposure", back_populates="asset", cascade="all, delete-orphan")
    access_reviews = relationship("AccessReview", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DataAsset(id={self.id}, name='{self.name}', type='{self.asset_type}')>"


class DataLineage(Base):
    """
    Data lineage relationships (upstream/downstream dependencies).
    
    Grain: One row per lineage relationship
    Type: Fact table (records relationships between assets)
    """
    __tablename__ = 'data_lineage'
    
    id = Column(Integer, primary_key=True)
    source_asset_id = Column(Integer, ForeignKey('data_assets.id'), nullable=False)
    target_asset_id = Column(Integer, ForeignKey('data_assets.id'), nullable=False)
    transformation_type = Column(String(100))  # ETL, query, API, copy
    transformation_details = Column(Text)  # SQL, script, or description
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_verified_at = Column(DateTime)
    verified_by = Column(String(255))
    
    # Relationships
    source_asset = relationship("DataAsset", foreign_keys=[source_asset_id], back_populates="lineage_as_source")
    target_asset = relationship("DataAsset", foreign_keys=[target_asset_id], back_populates="lineage_as_target")
    
    def __repr__(self):
        return f"<DataLineage(source={self.source_asset_id}, target={self.target_asset_id})>"


class PIIExposure(Base):
    """
    PII (Personally Identifiable Information) exposure tracking.
    
    Grain: One row per PII field in a data asset
    Type: Fact table (tracks PII fields and their classifications)
    """
    __tablename__ = 'pii_exposure'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('data_assets.id'), nullable=False)
    field_name = Column(String(255), nullable=False)  # Column name, field name
    pii_type = Column(String(100))  # SSN, email, name, phone, address, credit_card, etc.
    sensitivity_level = Column(String(50))  # public, internal, confidential, restricted
    encryption_status = Column(String(50))  # encrypted, unencrypted, tokenized
    retention_period_days = Column(Integer)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(255))
    
    # Relationships
    asset = relationship("DataAsset", back_populates="pii_records")
    
    def __repr__(self):
        return f"<PIIExposure(asset_id={self.asset_id}, field='{self.field_name}', type='{self.pii_type}')>"


class AccessReview(Base):
    """
    Access review records for data assets.
    
    Grain: One row per access review cycle per asset
    Type: Fact table with time-series (tracks review history)
    """
    __tablename__ = 'access_reviews'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('data_assets.id'), nullable=False)
    reviewer_email = Column(String(255), nullable=False)
    review_period_start = Column(DateTime, nullable=False)
    review_period_end = Column(DateTime, nullable=False)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    review_comments = Column(Text)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    
    # Relationships
    asset = relationship("DataAsset", back_populates="access_reviews")
    
    def __repr__(self):
        return f"<AccessReview(asset_id={self.asset_id}, reviewer='{self.reviewer_email}', status='{self.status.value}')>"


# ============================================================================
# SOX / AUDIT PREP MODELS
# ============================================================================

class AuditControl(Base):
    """
    Audit controls (SOX controls, internal controls).
    
    Grain: One row per control
    Type: Dimension table (SCD2 if control definitions change over time)
    """
    __tablename__ = 'audit_controls'
    
    id = Column(Integer, primary_key=True)
    control_id = Column(String(100), unique=True, nullable=False)  # e.g., "SOX-001"
    control_name = Column(String(255), nullable=False)
    control_description = Column(Text)
    control_owner_email = Column(String(255), nullable=False)
    framework = Column(SQLEnum(ComplianceFramework), nullable=False)  # SOX, SOC2, etc.
    control_type = Column(String(100))  # preventive, detective, corrective
    frequency = Column(String(50))  # daily, weekly, monthly, quarterly, annually
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    control_tests = relationship("ControlTest", back_populates="control", cascade="all, delete-orphan")
    evidence_records = relationship("EvidenceRecord", back_populates="control", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AuditControl(id={self.control_id}, name='{self.control_name}')>"


class ControlTest(Base):
    """
    Control testing records (test execution history).
    
    Grain: One row per test execution per control
    Type: Fact table with time-series (tracks test history)
    """
    __tablename__ = 'control_tests'
    
    id = Column(Integer, primary_key=True)
    control_id = Column(Integer, ForeignKey('audit_controls.id'), nullable=False)
    test_period_start = Column(DateTime, nullable=False)
    test_period_end = Column(DateTime, nullable=False)
    tester_email = Column(String(255), nullable=False)
    test_result = Column(String(50))  # pass, fail, exception
    test_notes = Column(Text)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    
    # Relationships
    control = relationship("AuditControl", back_populates="control_tests")
    
    def __repr__(self):
        return f"<ControlTest(control_id={self.control_id}, result='{self.test_result}', status='{self.status.value}')>"


class EvidenceRecord(Base):
    """
    Evidence collection records for controls.
    
    Grain: One row per evidence item per control
    Type: Fact table (tracks evidence artifacts)
    """
    __tablename__ = 'evidence_records'
    
    id = Column(Integer, primary_key=True)
    control_id = Column(Integer, ForeignKey('audit_controls.id'), nullable=False)
    evidence_name = Column(String(255), nullable=False)
    evidence_type = Column(String(100))  # document, screenshot, log, query_result, etc.
    file_path = Column(String(500))  # Path to stored evidence file
    collected_by = Column(String(255), nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow)
    evidence_period_start = Column(DateTime)  # What period does this evidence cover
    evidence_period_end = Column(DateTime)
    description = Column(Text)
    metadata = Column(JSON)  # Additional structured metadata
    
    # Relationships
    control = relationship("AuditControl", back_populates="evidence_records")
    
    def __repr__(self):
        return f"<EvidenceRecord(control_id={self.control_id}, name='{self.evidence_name}')>"


class ChangeTracking(Base):
    """
    Change tracking for controls, processes, and systems.
    
    Grain: One row per change event
    Type: Fact table with time-series (audit trail of changes)
    """
    __tablename__ = 'change_tracking'
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(100), nullable=False)  # control, process, system, configuration
    entity_id = Column(String(255), nullable=False)  # ID of the changed entity
    change_type = Column(String(100), nullable=False)  # created, updated, deleted
    changed_by = Column(String(255), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_description = Column(Text)
    old_values = Column(JSON)  # Snapshot of old values
    new_values = Column(JSON)  # Snapshot of new values
    approval_status = Column(String(50))  # pending, approved, rejected
    approved_by = Column(String(255))
    approved_at = Column(DateTime)
    
    def __repr__(self):
        return f"<ChangeTracking(entity_type='{self.entity_type}', entity_id='{self.entity_id}', change_type='{self.change_type}')>"


# ============================================================================
# VENDOR RISK / QUESTIONNAIRE MODELS
# ============================================================================

class Vendor(Base):
    """
    Vendor/third-party information.
    
    Grain: One row per vendor
    Type: Dimension table (SCD2 if vendor details change)
    """
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True)
    vendor_name = Column(String(255), unique=True, nullable=False)
    vendor_email = Column(String(255))
    vendor_website = Column(String(500))
    vendor_type = Column(String(100))  # SaaS, cloud, service_provider, etc.
    description = Column(Text)
    primary_contact_email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    questionnaires = relationship("Questionnaire", back_populates="vendor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vendor(name='{self.vendor_name}')>"


class Questionnaire(Base):
    """
    Security/compliance questionnaires sent to vendors.
    
    Grain: One row per questionnaire instance
    Type: Fact table (tracks questionnaire submissions)
    """
    __tablename__ = 'questionnaires'
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)
    framework = Column(SQLEnum(ComplianceFramework), nullable=False)  # SOC2, ISO, HIPAA
    questionnaire_type = Column(String(100))  # security, privacy, data_processing
    status = Column(String(50), default="draft")  # draft, sent, in_progress, completed, expired
    sent_at = Column(DateTime)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="questionnaires")
    responses = relationship("QuestionnaireResponse", back_populates="questionnaire", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Questionnaire(vendor_id={self.vendor_id}, framework='{self.framework.value}', status='{self.status}')>"


class QuestionnaireTemplate(Base):
    """
    Reusable questionnaire templates for different frameworks.
    
    Grain: One row per template
    Type: Dimension table (templates are reference data)
    """
    __tablename__ = 'questionnaire_templates'
    
    id = Column(Integer, primary_key=True)
    template_name = Column(String(255), nullable=False)
    framework = Column(SQLEnum(ComplianceFramework), nullable=False)
    template_json = Column(JSON, nullable=False)  # JSON schema defining questions
    version = Column(String(50), default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuestionnaireTemplate(name='{self.template_name}', framework='{self.framework.value}')>"


class QuestionnaireResponse(Base):
    """
    Individual responses to questionnaire questions.
    
    Grain: One row per question response per questionnaire
    Type: Fact table (stores all responses)
    """
    __tablename__ = 'questionnaire_responses'
    
    id = Column(Integer, primary_key=True)
    questionnaire_id = Column(Integer, ForeignKey('questionnaires.id'), nullable=False)
    question_id = Column(String(255), nullable=False)  # Question identifier from template
    question_text = Column(Text, nullable=False)
    response_value = Column(Text)  # Answer provided
    response_type = Column(String(50))  # text, yes_no, multiple_choice, file_upload
    response_metadata = Column(JSON)  # Additional structured data
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    questionnaire = relationship("Questionnaire", back_populates="responses")
    
    def __repr__(self):
        return f"<QuestionnaireResponse(questionnaire_id={self.questionnaire_id}, question_id='{self.question_id}')>"


class ResponseReuse(Base):
    """
    Tracks reusable responses across questionnaires (response library).
    
    Grain: One row per reusable response
    Type: Dimension table (library of standard responses)
    """
    __tablename__ = 'response_reuse'
    
    id = Column(Integer, primary_key=True)
    question_key = Column(String(255), nullable=False)  # Normalized question identifier
    framework = Column(SQLEnum(ComplianceFramework))
    standard_response = Column(Text, nullable=False)
    applicable_context = Column(Text)  # When to use this response
    last_used_at = Column(DateTime)
    use_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ResponseReuse(question_key='{self.question_key}', framework='{self.framework.value if self.framework else None}')>"


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database(db_path: str = "compliance_governance.db"):
    """
    Initialize the database and create all tables.
    
    Args:
        db_path: Path to SQLite database file
    """
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """
    Create a database session.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        Session object
    """
    Session = sessionmaker(bind=engine)
    return Session()

