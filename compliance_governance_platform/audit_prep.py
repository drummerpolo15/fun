"""
SOX / Internal Audit Prep Automation Module

This module handles:
- Evidence collection and storage
- Control testing reminders and scheduling
- Change tracking for controls, processes, and systems

Target: Finance & audit leaders preparing for SOX audits and internal audits
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import (
    AuditControl, ControlTest, EvidenceRecord, ChangeTracking,
    ComplianceFramework, ReviewStatus
)


class AuditPrepManager:
    """
    Main manager class for SOX/audit preparation operations.
    
    Handles CRUD operations for controls, control tests, evidence, and change tracking.
    """
    
    def __init__(self, session: Session):
        """
        Initialize the Audit Prep Manager.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    # ========================================================================
    # CONTROL MANAGEMENT
    # ========================================================================
    
    def create_control(
        self,
        control_id: str,
        control_name: str,
        control_owner_email: str,
        framework: ComplianceFramework,
        control_description: Optional[str] = None,
        control_type: Optional[str] = None,
        frequency: Optional[str] = None
    ) -> AuditControl:
        """
        Create a new audit control.
        
        Example controls:
        - SOX-001: User access reviews are performed quarterly
        - SOX-002: System changes require approval
        - SOC2-001: Encryption is enabled for data at rest
        
        Args:
            control_id: Unique control identifier (e.g., "SOX-001")
            control_name: Name of the control
            control_owner_email: Email of the control owner
            framework: Compliance framework (SOX, SOC2, ISO27001, etc.)
            control_description: Detailed description of the control
            control_type: Type of control (preventive, detective, corrective)
            frequency: Testing frequency (daily, weekly, monthly, quarterly, annually)
            
        Returns:
            Created AuditControl object
        """
        control = AuditControl(
            control_id=control_id,
            control_name=control_name,
            control_owner_email=control_owner_email,
            framework=framework,
            control_description=control_description,
            control_type=control_type,
            frequency=frequency
        )
        self.session.add(control)
        self.session.commit()
        self.session.refresh(control)
        return control
    
    def get_control(self, control_id: int) -> Optional[AuditControl]:
        """Get a control by ID."""
        return self.session.query(AuditControl).filter(AuditControl.id == control_id).first()
    
    def get_control_by_control_id(self, control_id: str) -> Optional[AuditControl]:
        """Get a control by its control_id (e.g., 'SOX-001')."""
        return self.session.query(AuditControl).filter(
            AuditControl.control_id == control_id
        ).first()
    
    def list_controls(
        self,
        framework: Optional[ComplianceFramework] = None,
        control_owner_email: Optional[str] = None,
        is_active: bool = True
    ) -> List[AuditControl]:
        """
        List controls with optional filters.
        
        Args:
            framework: Filter by compliance framework
            control_owner_email: Filter by control owner
            is_active: Filter by active status
            
        Returns:
            List of AuditControl objects
        """
        query = self.session.query(AuditControl).filter(AuditControl.is_active == is_active)
        
        if framework:
            query = query.filter(AuditControl.framework == framework)
        if control_owner_email:
            query = query.filter(AuditControl.control_owner_email == control_owner_email)
        
        return query.all()
    
    # ========================================================================
    # CONTROL TESTING
    # ========================================================================
    
    def create_control_test(
        self,
        control_id: int,
        tester_email: str,
        test_period_start: datetime,
        test_period_end: datetime,
        due_date: datetime
    ) -> ControlTest:
        """
        Create a control test record.
        
        Control tests verify that controls are operating effectively.
        Tests are typically scheduled based on the control's frequency.
        
        Args:
            control_id: ID of the control to test
            tester_email: Email of the person performing the test
            test_period_start: Start of the period being tested
            test_period_end: End of the period being tested
            due_date: When the test must be completed by
            
        Returns:
            Created ControlTest object
        """
        test = ControlTest(
            control_id=control_id,
            tester_email=tester_email,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
            due_date=due_date,
            status=ReviewStatus.PENDING
        )
        self.session.add(test)
        self.session.commit()
        self.session.refresh(test)
        return test
    
    def list_control_tests(
        self,
        control_id: Optional[int] = None,
        tester_email: Optional[str] = None,
        status: Optional[ReviewStatus] = None,
        overdue_only: bool = False
    ) -> List[ControlTest]:
        """
        List control tests with optional filters.
        
        Args:
            control_id: Filter by control ID
            tester_email: Filter by tester email
            status: Filter by test status
            overdue_only: Only return tests that are past due
            
        Returns:
            List of ControlTest objects
        """
        query = self.session.query(ControlTest)
        
        if control_id:
            query = query.filter(ControlTest.control_id == control_id)
        if tester_email:
            query = query.filter(ControlTest.tester_email == tester_email)
        if status:
            query = query.filter(ControlTest.status == status)
        if overdue_only:
            # Tests that are pending/in_progress and past due date
            query = query.filter(
                and_(
                    ControlTest.due_date < datetime.utcnow(),
                    ControlTest.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS])
                )
            )
        
        return query.all()
    
    def update_control_test(
        self,
        test_id: int,
        test_result: str,
        test_notes: Optional[str] = None,
        status: Optional[ReviewStatus] = None
    ) -> Optional[ControlTest]:
        """
        Update a control test with results.
        
        Args:
            test_id: ID of the test to update
            test_result: Test result (pass, fail, exception)
            test_notes: Notes about the test execution
            status: Status (if not provided, will be set based on result)
            
        Returns:
            Updated ControlTest object, or None if not found
        """
        test = self.session.query(ControlTest).filter(ControlTest.id == test_id).first()
        if not test:
            return None
        
        test.test_result = test_result
        if test_notes:
            test.test_notes = test_notes
        
        # Set status based on result if not explicitly provided
        if status:
            test.status = status
        elif test_result == "pass":
            test.status = ReviewStatus.APPROVED
        elif test_result == "fail":
            test.status = ReviewStatus.REJECTED
        
        test.completed_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(test)
        return test
    
    def get_overdue_tests(self) -> List[ControlTest]:
        """
        Get all overdue control tests.
        
        Returns:
            List of ControlTest objects that are past due
        """
        return self.list_control_tests(overdue_only=True)
    
    def generate_test_reminders(self, days_ahead: int = 7) -> List[ControlTest]:
        """
        Generate test reminders for tests due in the next N days.
        
        Useful for sending reminder emails/notifications to testers.
        
        Args:
            days_ahead: Number of days ahead to look for due tests
            
        Returns:
            List of ControlTest objects due in the next N days
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        return self.session.query(ControlTest).filter(
            and_(
                ControlTest.due_date <= cutoff_date,
                ControlTest.due_date >= datetime.utcnow(),
                ControlTest.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS])
            )
        ).all()
    
    # ========================================================================
    # EVIDENCE COLLECTION
    # ========================================================================
    
    def create_evidence_record(
        self,
        control_id: int,
        evidence_name: str,
        collected_by: str,
        evidence_type: Optional[str] = None,
        file_path: Optional[str] = None,
        evidence_period_start: Optional[datetime] = None,
        evidence_period_end: Optional[datetime] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> EvidenceRecord:
        """
        Create an evidence record.
        
        Evidence is collected to support control testing and audit assertions.
        Examples: screenshots, log files, query results, system reports.
        
        Args:
            control_id: ID of the control this evidence supports
            evidence_name: Name/title of the evidence
            collected_by: Email of person who collected the evidence
            evidence_type: Type of evidence (document, screenshot, log, query_result, etc.)
            file_path: Path to stored evidence file
            evidence_period_start: Start of period covered by evidence
            evidence_period_end: End of period covered by evidence
            description: Description of the evidence
            metadata: Additional structured metadata (JSON)
            
        Returns:
            Created EvidenceRecord object
        """
        evidence = EvidenceRecord(
            control_id=control_id,
            evidence_name=evidence_name,
            collected_by=collected_by,
            evidence_type=evidence_type,
            file_path=file_path,
            evidence_period_start=evidence_period_start,
            evidence_period_end=evidence_period_end,
            description=description,
            metadata=metadata
        )
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)
        return evidence
    
    def list_evidence_records(
        self,
        control_id: Optional[int] = None,
        collected_by: Optional[str] = None,
        evidence_type: Optional[str] = None
    ) -> List[EvidenceRecord]:
        """
        List evidence records with optional filters.
        
        Args:
            control_id: Filter by control ID
            collected_by: Filter by collector email
            evidence_type: Filter by evidence type
            
        Returns:
            List of EvidenceRecord objects
        """
        query = self.session.query(EvidenceRecord)
        
        if control_id:
            query = query.filter(EvidenceRecord.control_id == control_id)
        if collected_by:
            query = query.filter(EvidenceRecord.collected_by == collected_by)
        if evidence_type:
            query = query.filter(EvidenceRecord.evidence_type == evidence_type)
        
        return query.order_by(EvidenceRecord.collected_at.desc()).all()
    
    def get_evidence_for_control(self, control_id: int) -> List[EvidenceRecord]:
        """
        Get all evidence records for a specific control.
        
        Args:
            control_id: ID of the control
            
        Returns:
            List of EvidenceRecord objects for the control
        """
        return self.list_evidence_records(control_id=control_id)
    
    # ========================================================================
    # CHANGE TRACKING
    # ========================================================================
    
    def track_change(
        self,
        entity_type: str,
        entity_id: str,
        change_type: str,
        changed_by: str,
        change_description: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None
    ) -> ChangeTracking:
        """
        Track a change to a control, process, or system.
        
        Change tracking creates an audit trail of modifications.
        This is critical for SOX compliance and internal audits.
        
        Args:
            entity_type: Type of entity (control, process, system, configuration)
            entity_id: ID of the entity that changed
            change_type: Type of change (created, updated, deleted)
            changed_by: Email of person who made the change
            change_description: Description of the change
            old_values: Snapshot of old values (JSON)
            new_values: Snapshot of new values (JSON)
            
        Returns:
            Created ChangeTracking object
        """
        change = ChangeTracking(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type,
            changed_by=changed_by,
            change_description=change_description,
            old_values=old_values,
            new_values=new_values,
            approval_status="pending"
        )
        self.session.add(change)
        self.session.commit()
        self.session.refresh(change)
        return change
    
    def list_changes(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        change_type: Optional[str] = None,
        changed_by: Optional[str] = None,
        approval_status: Optional[str] = None
    ) -> List[ChangeTracking]:
        """
        List change tracking records with optional filters.
        
        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            change_type: Filter by change type
            changed_by: Filter by person who made the change
            approval_status: Filter by approval status
            
        Returns:
            List of ChangeTracking objects
        """
        query = self.session.query(ChangeTracking)
        
        if entity_type:
            query = query.filter(ChangeTracking.entity_type == entity_type)
        if entity_id:
            query = query.filter(ChangeTracking.entity_id == entity_id)
        if change_type:
            query = query.filter(ChangeTracking.change_type == change_type)
        if changed_by:
            query = query.filter(ChangeTracking.changed_by == changed_by)
        if approval_status:
            query = query.filter(ChangeTracking.approval_status == approval_status)
        
        return query.order_by(ChangeTracking.changed_at.desc()).all()
    
    def approve_change(
        self,
        change_id: int,
        approved_by: str
    ) -> Optional[ChangeTracking]:
        """
        Approve a change.
        
        Args:
            change_id: ID of the change to approve
            approved_by: Email of person approving the change
            
        Returns:
            Updated ChangeTracking object, or None if not found
        """
        change = self.session.query(ChangeTracking).filter(
            ChangeTracking.id == change_id
        ).first()
        if not change:
            return None
        
        change.approval_status = "approved"
        change.approved_by = approved_by
        change.approved_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(change)
        return change
    
    def get_change_history(self, entity_type: str, entity_id: str) -> List[ChangeTracking]:
        """
        Get change history for a specific entity.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            
        Returns:
            List of ChangeTracking objects for the entity
        """
        return self.list_changes(entity_type=entity_type, entity_id=entity_id)
    
    # ========================================================================
    # REPORTING / ANALYTICS
    # ========================================================================
    
    def get_audit_prep_summary(self, framework: Optional[ComplianceFramework] = None) -> Dict:
        """
        Get a summary of audit prep metrics.
        
        Args:
            framework: Optional framework filter
            
        Returns:
            Dictionary with summary statistics
        """
        query = self.session.query(AuditControl).filter(AuditControl.is_active == True)
        if framework:
            query = query.filter(AuditControl.framework == framework)
        total_controls = query.count()
        
        query = self.session.query(ControlTest)
        if framework:
            # Join with AuditControl to filter by framework
            query = query.join(AuditControl).filter(AuditControl.framework == framework)
        pending_tests = query.filter(ControlTest.status == ReviewStatus.PENDING).count()
        overdue_tests = len(self.get_overdue_tests())
        
        query = self.session.query(EvidenceRecord)
        if framework:
            query = query.join(AuditControl).filter(AuditControl.framework == framework)
        total_evidence = query.count()
        
        pending_changes = self.session.query(ChangeTracking).filter(
            ChangeTracking.approval_status == "pending"
        ).count()
        
        return {
            'total_controls': total_controls,
            'pending_control_tests': pending_tests,
            'overdue_control_tests': overdue_tests,
            'total_evidence_records': total_evidence,
            'pending_change_approvals': pending_changes
        }

