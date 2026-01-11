"""
Vendor Risk / Security Questionnaire Automation Module

This module handles:
- Vendor management
- Security/compliance questionnaire templates (SOC2, ISO, HIPAA)
- Questionnaire response collection and storage
- Response reuse library (standard responses that can be reused across questionnaires)

Target: Companies managing vendor risk assessments and security questionnaires
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import (
    Vendor, Questionnaire, QuestionnaireTemplate, QuestionnaireResponse,
    ResponseReuse, ComplianceFramework
)


class VendorRiskManager:
    """
    Main manager class for vendor risk and questionnaire operations.
    
    Handles CRUD operations for vendors, questionnaires, templates, responses, and response reuse.
    """
    
    def __init__(self, session: Session):
        """
        Initialize the Vendor Risk Manager.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    # ========================================================================
    # VENDOR MANAGEMENT
    # ========================================================================
    
    def create_vendor(
        self,
        vendor_name: str,
        vendor_email: Optional[str] = None,
        vendor_website: Optional[str] = None,
        vendor_type: Optional[str] = None,
        description: Optional[str] = None,
        primary_contact_email: Optional[str] = None
    ) -> Vendor:
        """
        Create a new vendor record.
        
        Args:
            vendor_name: Name of the vendor
            vendor_email: Vendor's general email
            vendor_website: Vendor's website URL
            vendor_type: Type of vendor (SaaS, cloud, service_provider, etc.)
            description: Description of the vendor
            primary_contact_email: Email of primary contact person
            
        Returns:
            Created Vendor object
        """
        vendor = Vendor(
            vendor_name=vendor_name,
            vendor_email=vendor_email,
            vendor_website=vendor_website,
            vendor_type=vendor_type,
            description=description,
            primary_contact_email=primary_contact_email
        )
        self.session.add(vendor)
        self.session.commit()
        self.session.refresh(vendor)
        return vendor
    
    def get_vendor(self, vendor_id: int) -> Optional[Vendor]:
        """Get a vendor by ID."""
        return self.session.query(Vendor).filter(Vendor.id == vendor_id).first()
    
    def list_vendors(self, is_active: bool = True) -> List[Vendor]:
        """
        List vendors.
        
        Args:
            is_active: Filter by active status
            
        Returns:
            List of Vendor objects
        """
        return self.session.query(Vendor).filter(Vendor.is_active == is_active).all()
    
    # ========================================================================
    # QUESTIONNAIRE TEMPLATES
    # ========================================================================
    
    def create_questionnaire_template(
        self,
        template_name: str,
        framework: ComplianceFramework,
        template_json: Dict,
        version: str = "1.0"
    ) -> QuestionnaireTemplate:
        """
        Create a questionnaire template.
        
        Templates define the structure and questions for different frameworks.
        The template_json should follow a schema like:
        {
            "questions": [
                {
                    "id": "Q1",
                    "text": "Do you encrypt data at rest?",
                    "type": "yes_no",
                    "required": true
                },
                {
                    "id": "Q2",
                    "text": "Describe your encryption method",
                    "type": "text",
                    "required": false
                }
            ]
        }
        
        Args:
            template_name: Name of the template
            framework: Compliance framework (SOC2, ISO27001, HIPAA, etc.)
            template_json: JSON structure defining the questions
            version: Template version
            
        Returns:
            Created QuestionnaireTemplate object
        """
        template = QuestionnaireTemplate(
            template_name=template_name,
            framework=framework,
            template_json=template_json,
            version=version
        )
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template
    
    def get_template(self, template_id: int) -> Optional[QuestionnaireTemplate]:
        """Get a template by ID."""
        return self.session.query(QuestionnaireTemplate).filter(
            QuestionnaireTemplate.id == template_id
        ).first()
    
    def get_template_by_framework(
        self,
        framework: ComplianceFramework,
        is_active: bool = True
    ) -> Optional[QuestionnaireTemplate]:
        """
        Get the active template for a framework.
        
        Args:
            framework: Compliance framework
            is_active: Filter by active status
            
        Returns:
            QuestionnaireTemplate object, or None if not found
        """
        return self.session.query(QuestionnaireTemplate).filter(
            and_(
                QuestionnaireTemplate.framework == framework,
                QuestionnaireTemplate.is_active == is_active
            )
        ).order_by(QuestionnaireTemplate.version.desc()).first()
    
    def list_templates(
        self,
        framework: Optional[ComplianceFramework] = None,
        is_active: bool = True
    ) -> List[QuestionnaireTemplate]:
        """
        List questionnaire templates.
        
        Args:
            framework: Filter by framework
            is_active: Filter by active status
            
        Returns:
            List of QuestionnaireTemplate objects
        """
        query = self.session.query(QuestionnaireTemplate).filter(
            QuestionnaireTemplate.is_active == is_active
        )
        if framework:
            query = query.filter(QuestionnaireTemplate.framework == framework)
        return query.all()
    
    # ========================================================================
    # QUESTIONNAIRE MANAGEMENT
    # ========================================================================
    
    def create_questionnaire(
        self,
        vendor_id: int,
        framework: ComplianceFramework,
        created_by: str,
        questionnaire_type: Optional[str] = None,
        due_date: Optional[datetime] = None
    ) -> Questionnaire:
        """
        Create a new questionnaire for a vendor.
        
        Args:
            vendor_id: ID of the vendor
            framework: Compliance framework (SOC2, ISO, HIPAA, etc.)
            created_by: Email of person creating the questionnaire
            questionnaire_type: Type of questionnaire (security, privacy, data_processing)
            due_date: When the questionnaire is due
            
        Returns:
            Created Questionnaire object
        """
        questionnaire = Questionnaire(
            vendor_id=vendor_id,
            framework=framework,
            created_by=created_by,
            questionnaire_type=questionnaire_type,
            due_date=due_date,
            status="draft"
        )
        self.session.add(questionnaire)
        self.session.commit()
        self.session.refresh(questionnaire)
        return questionnaire
    
    def get_questionnaire(self, questionnaire_id: int) -> Optional[Questionnaire]:
        """Get a questionnaire by ID."""
        return self.session.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id
        ).first()
    
    def list_questionnaires(
        self,
        vendor_id: Optional[int] = None,
        framework: Optional[ComplianceFramework] = None,
        status: Optional[str] = None
    ) -> List[Questionnaire]:
        """
        List questionnaires with optional filters.
        
        Args:
            vendor_id: Filter by vendor ID
            framework: Filter by framework
            status: Filter by status (draft, sent, in_progress, completed, expired)
            
        Returns:
            List of Questionnaire objects
        """
        query = self.session.query(Questionnaire)
        
        if vendor_id:
            query = query.filter(Questionnaire.vendor_id == vendor_id)
        if framework:
            query = query.filter(Questionnaire.framework == framework)
        if status:
            query = query.filter(Questionnaire.status == status)
        
        return query.order_by(Questionnaire.created_at.desc()).all()
    
    def send_questionnaire(self, questionnaire_id: int) -> Optional[Questionnaire]:
        """
        Mark a questionnaire as sent.
        
        Args:
            questionnaire_id: ID of the questionnaire
            
        Returns:
            Updated Questionnaire object, or None if not found
        """
        questionnaire = self.get_questionnaire(questionnaire_id)
        if not questionnaire:
            return None
        
        questionnaire.status = "sent"
        questionnaire.sent_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(questionnaire)
        return questionnaire
    
    def mark_questionnaire_completed(self, questionnaire_id: int) -> Optional[Questionnaire]:
        """
        Mark a questionnaire as completed.
        
        Args:
            questionnaire_id: ID of the questionnaire
            
        Returns:
            Updated Questionnaire object, or None if not found
        """
        questionnaire = self.get_questionnaire(questionnaire_id)
        if not questionnaire:
            return None
        
        questionnaire.status = "completed"
        questionnaire.completed_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(questionnaire)
        return questionnaire
    
    # ========================================================================
    # QUESTIONNAIRE RESPONSES
    # ========================================================================
    
    def create_response(
        self,
        questionnaire_id: int,
        question_id: str,
        question_text: str,
        response_value: str,
        response_type: str = "text"
    ) -> QuestionnaireResponse:
        """
        Create a questionnaire response.
        
        Args:
            questionnaire_id: ID of the questionnaire
            question_id: Question identifier (from template)
            question_text: The question text
            response_value: The response/answer
            response_type: Type of response (text, yes_no, multiple_choice, file_upload)
            
        Returns:
            Created QuestionnaireResponse object
        """
        response = QuestionnaireResponse(
            questionnaire_id=questionnaire_id,
            question_id=question_id,
            question_text=question_text,
            response_value=response_value,
            response_type=response_type
        )
        self.session.add(response)
        self.session.commit()
        self.session.refresh(response)
        return response
    
    def get_responses(self, questionnaire_id: int) -> List[QuestionnaireResponse]:
        """
        Get all responses for a questionnaire.
        
        Args:
            questionnaire_id: ID of the questionnaire
            
        Returns:
            List of QuestionnaireResponse objects
        """
        return self.session.query(QuestionnaireResponse).filter(
            QuestionnaireResponse.questionnaire_id == questionnaire_id
        ).order_by(QuestionnaireResponse.question_id).all()
    
    def update_response(
        self,
        response_id: int,
        response_value: str
    ) -> Optional[QuestionnaireResponse]:
        """
        Update a questionnaire response.
        
        Args:
            response_id: ID of the response to update
            response_value: New response value
            
        Returns:
            Updated QuestionnaireResponse object, or None if not found
        """
        response = self.session.query(QuestionnaireResponse).filter(
            QuestionnaireResponse.id == response_id
        ).first()
        if not response:
            return None
        
        response.response_value = response_value
        response.answered_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(response)
        return response
    
    # ========================================================================
    # RESPONSE REUSE LIBRARY
    # ========================================================================
    
    def create_reusable_response(
        self,
        question_key: str,
        standard_response: str,
        framework: Optional[ComplianceFramework] = None,
        applicable_context: Optional[str] = None
    ) -> ResponseReuse:
        """
        Create a reusable response in the response library.
        
        Response reuse allows standard answers to common questions
        to be reused across multiple questionnaires, saving time.
        
        Args:
            question_key: Normalized question identifier/key
            standard_response: Standard response text
            framework: Optional framework this response applies to
            applicable_context: Description of when to use this response
            
        Returns:
            Created ResponseReuse object
        """
        response = ResponseReuse(
            question_key=question_key,
            standard_response=standard_response,
            framework=framework,
            applicable_context=applicable_context
        )
        self.session.add(response)
        self.session.commit()
        self.session.refresh(response)
        return response
    
    def get_reusable_response(
        self,
        question_key: str,
        framework: Optional[ComplianceFramework] = None
    ) -> Optional[ResponseReuse]:
        """
        Get a reusable response by question key.
        
        Args:
            question_key: Question key to search for
            framework: Optional framework filter
            
        Returns:
            ResponseReuse object, or None if not found
        """
        query = self.session.query(ResponseReuse).filter(
            ResponseReuse.question_key == question_key
        )
        if framework:
            query = query.filter(ResponseReuse.framework == framework)
        return query.first()
    
    def list_reusable_responses(
        self,
        framework: Optional[ComplianceFramework] = None
    ) -> List[ResponseReuse]:
        """
        List reusable responses.
        
        Args:
            framework: Optional framework filter
            
        Returns:
            List of ResponseReuse objects
        """
        query = self.session.query(ResponseReuse)
        if framework:
            query = query.filter(ResponseReuse.framework == framework)
        return query.all()
    
    def use_reusable_response(
        self,
        question_key: str,
        framework: Optional[ComplianceFramework] = None
    ) -> Optional[str]:
        """
        Use a reusable response and increment its use count.
        
        Args:
            question_key: Question key to get response for
            framework: Optional framework filter
            
        Returns:
            Standard response text, or None if not found
        """
        response = self.get_reusable_response(question_key, framework)
        if not response:
            return None
        
        # Increment use count and update last used timestamp
        response.use_count += 1
        response.last_used_at = datetime.utcnow()
        self.session.commit()
        
        return response.standard_response
    
    def map_question_to_response(
        self,
        question_text: str,
        framework: ComplianceFramework
    ) -> Optional[str]:
        """
        Map a question text to a reusable response (simple keyword matching).
        
        This is a simplified version. In production, you might use
        NLP/ML for better question matching.
        
        Args:
            question_text: The question text
            framework: Compliance framework
            
        Returns:
            Standard response text if match found, None otherwise
        """
        # Simple keyword-based matching (can be enhanced with NLP)
        # Look for common question patterns
        question_lower = question_text.lower()
        
        # Check reusable responses for this framework
        reusable_responses = self.list_reusable_responses(framework)
        
        # Try to match by question key or keywords in question text
        for response in reusable_responses:
            # Simple matching - in production, use better NLP
            if response.question_key.lower() in question_lower:
                return self.use_reusable_response(response.question_key, framework)
        
        return None
    
    # ========================================================================
    # COMPLIANCE FRAMEWORK MAPPING
    # ========================================================================
    
    def map_responses_across_frameworks(
        self,
        source_framework: ComplianceFramework,
        target_framework: ComplianceFramework,
        questionnaire_id: int
    ) -> Dict:
        """
        Map questionnaire responses from one framework to another.
        
        This helps when a vendor has already completed a SOC2 questionnaire
        and you want to reuse responses for an ISO questionnaire.
        
        Args:
            source_framework: Framework of the source questionnaire
            target_framework: Framework to map to
            questionnaire_id: ID of the source questionnaire
            
        Returns:
            Dictionary with mapped responses
        """
        # Get source questionnaire responses
        source_responses = self.get_responses(questionnaire_id)
        
        # This is a simplified mapping - in production, you would have
        # a mapping table/config that maps questions across frameworks
        mapped_responses = {}
        
        for response in source_responses:
            # Try to find equivalent question in target framework
            # In production, use a mapping table/config
            mapped_responses[response.question_id] = {
                'source_question': response.question_text,
                'response': response.response_value,
                'target_question_id': None  # Would be populated from mapping table
            }
        
        return {
            'source_framework': source_framework.value,
            'target_framework': target_framework.value,
            'mapped_responses': mapped_responses
        }
    
    # ========================================================================
    # REPORTING / ANALYTICS
    # ========================================================================
    
    def get_vendor_risk_summary(self) -> Dict:
        """
        Get a summary of vendor risk metrics.
        
        Returns:
            Dictionary with summary statistics
        """
        total_vendors = self.session.query(Vendor).filter(Vendor.is_active == True).count()
        total_questionnaires = self.session.query(Questionnaire).count()
        
        pending_questionnaires = self.session.query(Questionnaire).filter(
            Questionnaire.status.in_(["draft", "sent", "in_progress"])
        ).count()
        
        overdue_questionnaires = self.session.query(Questionnaire).filter(
            and_(
                Questionnaire.due_date < datetime.utcnow(),
                Questionnaire.status.in_(["sent", "in_progress"])
            )
        ).count()
        
        total_templates = self.session.query(QuestionnaireTemplate).filter(
            QuestionnaireTemplate.is_active == True
        ).count()
        
        total_reusable_responses = self.session.query(ResponseReuse).count()
        
        return {
            'total_vendors': total_vendors,
            'total_questionnaires': total_questionnaires,
            'pending_questionnaires': pending_questionnaires,
            'overdue_questionnaires': overdue_questionnaires,
            'total_templates': total_templates,
            'total_reusable_responses': total_reusable_responses
        }

