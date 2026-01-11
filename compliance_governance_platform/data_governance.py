"""
Data Governance Automation Module

This module handles:
- Data lineage tracking (upstream/downstream dependencies)
- Data ownership management
- PII (Personally Identifiable Information) exposure tracking
- Access reviews and certifications

Target: Mid-market companies (200-2,000 employees)
Positioning: Between overbuilt tools (Collibra) and underpowered (spreadsheets)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import (
    DataAsset, DataLineage, PIIExposure, AccessReview,
    ReviewStatus
)


class DataGovernanceManager:
    """
    Main manager class for data governance operations.
    
    Handles CRUD operations for data assets, lineage, PII tracking, and access reviews.
    """
    
    def __init__(self, session: Session):
        """
        Initialize the Data Governance Manager.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    # ========================================================================
    # DATA ASSET MANAGEMENT
    # ========================================================================
    
    def create_data_asset(
        self,
        name: str,
        asset_type: str,
        location: str,
        description: Optional[str] = None,
        owner_email: Optional[str] = None,
        steward_email: Optional[str] = None
    ) -> DataAsset:
        """
        Create a new data asset record.
        
        Args:
            name: Name of the data asset (e.g., "customers table", "sales_data.csv")
            asset_type: Type of asset (table, file, database, api)
            location: Location/identifier (database name, file path, API endpoint)
            description: Optional description
            owner_email: Email of the data owner
            steward_email: Email of the data steward
            
        Returns:
            Created DataAsset object
        """
        asset = DataAsset(
            name=name,
            asset_type=asset_type,
            location=location,
            description=description,
            owner_email=owner_email,
            steward_email=steward_email
        )
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset
    
    def get_data_asset(self, asset_id: int) -> Optional[DataAsset]:
        """Get a data asset by ID."""
        return self.session.query(DataAsset).filter(DataAsset.id == asset_id).first()
    
    def list_data_assets(
        self,
        asset_type: Optional[str] = None,
        owner_email: Optional[str] = None,
        is_active: bool = True
    ) -> List[DataAsset]:
        """
        List data assets with optional filters.
        
        Args:
            asset_type: Filter by asset type
            owner_email: Filter by owner email
            is_active: Filter by active status
            
        Returns:
            List of DataAsset objects
        """
        query = self.session.query(DataAsset).filter(DataAsset.is_active == is_active)
        
        if asset_type:
            query = query.filter(DataAsset.asset_type == asset_type)
        if owner_email:
            query = query.filter(DataAsset.owner_email == owner_email)
        
        return query.all()
    
    def update_data_asset_ownership(
        self,
        asset_id: int,
        owner_email: Optional[str] = None,
        steward_email: Optional[str] = None
    ) -> Optional[DataAsset]:
        """
        Update ownership information for a data asset.
        
        Note: For historical tracking (SCD2), you would create a new record
        with effective dates rather than updating in place. This is a simplified version.
        
        Args:
            asset_id: ID of the asset to update
            owner_email: New owner email
            steward_email: New steward email
            
        Returns:
            Updated DataAsset object, or None if not found
        """
        asset = self.get_data_asset(asset_id)
        if not asset:
            return None
        
        if owner_email is not None:
            asset.owner_email = owner_email
        if steward_email is not None:
            asset.steward_email = steward_email
        
        asset.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(asset)
        return asset
    
    # ========================================================================
    # DATA LINEAGE MANAGEMENT
    # ========================================================================
    
    def create_lineage(
        self,
        source_asset_id: int,
        target_asset_id: int,
        transformation_type: str,
        transformation_details: Optional[str] = None,
        verified_by: Optional[str] = None
    ) -> DataLineage:
        """
        Create a data lineage relationship.
        
        This tracks how data flows from source to target assets.
        Example: customers table -> sales_analytics view (via SQL query)
        
        Args:
            source_asset_id: ID of the source data asset
            target_asset_id: ID of the target data asset
            transformation_type: Type of transformation (ETL, query, API, copy)
            transformation_details: Details about the transformation (SQL, script, description)
            verified_by: Email of person who verified this lineage
            
        Returns:
            Created DataLineage object
        """
        lineage = DataLineage(
            source_asset_id=source_asset_id,
            target_asset_id=target_asset_id,
            transformation_type=transformation_type,
            transformation_details=transformation_details,
            verified_by=verified_by,
            last_verified_at=datetime.utcnow() if verified_by else None
        )
        self.session.add(lineage)
        self.session.commit()
        self.session.refresh(lineage)
        return lineage
    
    def get_downstream_lineage(self, asset_id: int) -> List[DataLineage]:
        """
        Get all downstream dependencies (assets that depend on this asset).
        
        Args:
            asset_id: ID of the source asset
            
        Returns:
            List of DataLineage objects where this asset is the source
        """
        return self.session.query(DataLineage).filter(
            DataLineage.source_asset_id == asset_id
        ).all()
    
    def get_upstream_lineage(self, asset_id: int) -> List[DataLineage]:
        """
        Get all upstream dependencies (assets this asset depends on).
        
        Args:
            asset_id: ID of the target asset
            
        Returns:
            List of DataLineage objects where this asset is the target
        """
        return self.session.query(DataLineage).filter(
            DataLineage.target_asset_id == asset_id
        ).all()
    
    def get_full_lineage_tree(self, asset_id: int) -> Dict:
        """
        Get the full lineage tree (both upstream and downstream) for an asset.
        
        Args:
            asset_id: ID of the asset
            
        Returns:
            Dictionary with 'upstream' and 'downstream' lineage lists
        """
        asset = self.get_data_asset(asset_id)
        if not asset:
            return {'upstream': [], 'downstream': []}
        
        return {
            'asset': asset,
            'upstream': self.get_upstream_lineage(asset_id),
            'downstream': self.get_downstream_lineage(asset_id)
        }
    
    # ========================================================================
    # PII EXPOSURE TRACKING
    # ========================================================================
    
    def record_pii_exposure(
        self,
        asset_id: int,
        field_name: str,
        pii_type: str,
        sensitivity_level: str = "confidential",
        encryption_status: str = "unencrypted",
        retention_period_days: Optional[int] = None,
        reviewed_by: Optional[str] = None
    ) -> PIIExposure:
        """
        Record PII exposure for a field in a data asset.
        
        Args:
            asset_id: ID of the data asset
            field_name: Name of the field/column containing PII
            pii_type: Type of PII (SSN, email, name, phone, address, credit_card, etc.)
            sensitivity_level: Sensitivity level (public, internal, confidential, restricted)
            encryption_status: Encryption status (encrypted, unencrypted, tokenized)
            retention_period_days: Retention period in days
            reviewed_by: Email of person who reviewed/verified this
            
        Returns:
            Created PIIExposure object
        """
        pii_record = PIIExposure(
            asset_id=asset_id,
            field_name=field_name,
            pii_type=pii_type,
            sensitivity_level=sensitivity_level,
            encryption_status=encryption_status,
            retention_period_days=retention_period_days,
            reviewed_by=reviewed_by,
            reviewed_at=datetime.utcnow() if reviewed_by else None
        )
        self.session.add(pii_record)
        self.session.commit()
        self.session.refresh(pii_record)
        return pii_record
    
    def list_pii_exposures(
        self,
        asset_id: Optional[int] = None,
        pii_type: Optional[str] = None,
        sensitivity_level: Optional[str] = None,
        encryption_status: Optional[str] = None
    ) -> List[PIIExposure]:
        """
        List PII exposures with optional filters.
        
        Useful for:
        - Finding all unencrypted PII (security risk)
        - Finding all restricted sensitivity data
        - Getting PII inventory for a specific asset
        
        Args:
            asset_id: Filter by asset ID
            pii_type: Filter by PII type
            sensitivity_level: Filter by sensitivity level
            encryption_status: Filter by encryption status
            
        Returns:
            List of PIIExposure objects
        """
        query = self.session.query(PIIExposure)
        
        if asset_id:
            query = query.filter(PIIExposure.asset_id == asset_id)
        if pii_type:
            query = query.filter(PIIExposure.pii_type == pii_type)
        if sensitivity_level:
            query = query.filter(PIIExposure.sensitivity_level == sensitivity_level)
        if encryption_status:
            query = query.filter(PIIExposure.encryption_status == encryption_status)
        
        return query.all()
    
    def get_unencrypted_pii(self) -> List[PIIExposure]:
        """
        Get all unencrypted PII exposures (security risk).
        
        Returns:
            List of unencrypted PIIExposure objects
        """
        return self.list_pii_exposures(encryption_status="unencrypted")
    
    # ========================================================================
    # ACCESS REVIEWS
    # ========================================================================
    
    def create_access_review(
        self,
        asset_id: int,
        reviewer_email: str,
        review_period_start: datetime,
        review_period_end: datetime,
        due_date: datetime
    ) -> AccessReview:
        """
        Create an access review record.
        
        Access reviews are periodic certifications where data owners/stewards
        review who has access to data assets and verify appropriateness.
        
        Args:
            asset_id: ID of the data asset to review
            reviewer_email: Email of the person conducting the review
            review_period_start: Start of the review period
            review_period_end: End of the review period
            due_date: When the review must be completed by
            
        Returns:
            Created AccessReview object
        """
        review = AccessReview(
            asset_id=asset_id,
            reviewer_email=reviewer_email,
            review_period_start=review_period_start,
            review_period_end=review_period_end,
            due_date=due_date,
            status=ReviewStatus.PENDING
        )
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review
    
    def list_access_reviews(
        self,
        asset_id: Optional[int] = None,
        reviewer_email: Optional[str] = None,
        status: Optional[ReviewStatus] = None,
        overdue_only: bool = False
    ) -> List[AccessReview]:
        """
        List access reviews with optional filters.
        
        Args:
            asset_id: Filter by asset ID
            reviewer_email: Filter by reviewer email
            status: Filter by review status
            overdue_only: Only return reviews that are past due
            
        Returns:
            List of AccessReview objects
        """
        query = self.session.query(AccessReview)
        
        if asset_id:
            query = query.filter(AccessReview.asset_id == asset_id)
        if reviewer_email:
            query = query.filter(AccessReview.reviewer_email == reviewer_email)
        if status:
            query = query.filter(AccessReview.status == status)
        if overdue_only:
            # Reviews that are pending/in_progress and past due date
            query = query.filter(
                and_(
                    AccessReview.due_date < datetime.utcnow(),
                    AccessReview.status.in_([ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS])
                )
            )
        
        return query.all()
    
    def update_access_review_status(
        self,
        review_id: int,
        status: ReviewStatus,
        review_comments: Optional[str] = None
    ) -> Optional[AccessReview]:
        """
        Update the status of an access review.
        
        Args:
            review_id: ID of the review to update
            status: New status (PENDING, IN_PROGRESS, APPROVED, REJECTED)
            review_comments: Optional comments from the reviewer
            
        Returns:
            Updated AccessReview object, or None if not found
        """
        review = self.session.query(AccessReview).filter(AccessReview.id == review_id).first()
        if not review:
            return None
        
        review.status = status
        if review_comments:
            review.review_comments = review_comments
        
        if status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            review.completed_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(review)
        return review
    
    def get_overdue_reviews(self) -> List[AccessReview]:
        """
        Get all overdue access reviews.
        
        Returns:
            List of AccessReview objects that are past due
        """
        return self.list_access_reviews(overdue_only=True)
    
    # ========================================================================
    # REPORTING / ANALYTICS
    # ========================================================================
    
    def get_governance_summary(self) -> Dict:
        """
        Get a summary of data governance metrics.
        
        Returns:
            Dictionary with summary statistics
        """
        total_assets = self.session.query(DataAsset).filter(DataAsset.is_active == True).count()
        assets_without_owner = self.session.query(DataAsset).filter(
            and_(
                DataAsset.is_active == True,
                or_(DataAsset.owner_email == None, DataAsset.owner_email == "")
            )
        ).count()
        
        total_lineage = self.session.query(DataLineage).count()
        total_pii_records = self.session.query(PIIExposure).count()
        unencrypted_pii = len(self.get_unencrypted_pii())
        
        pending_reviews = self.session.query(AccessReview).filter(
            AccessReview.status == ReviewStatus.PENDING
        ).count()
        overdue_reviews = len(self.get_overdue_reviews())
        
        return {
            'total_assets': total_assets,
            'assets_without_owner': assets_without_owner,
            'total_lineage_relationships': total_lineage,
            'total_pii_fields': total_pii_records,
            'unencrypted_pii_fields': unencrypted_pii,
            'pending_access_reviews': pending_reviews,
            'overdue_access_reviews': overdue_reviews
        }

