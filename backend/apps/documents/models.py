"""
Document model for RAG knowledge base.
"""

import uuid
from django.db import models
# from django.contrib.postgres.fields import ArrayField
ArrayField = lambda field, **kwargs: models.JSONField(**kwargs)
from django.utils.translation import gettext_lazy as _
# from pgvector.django import VectorField
def VectorField(dimensions=None, **kwargs):
    return models.JSONField(**kwargs)

from apps.tenants.models import Tenant


class ContentType:
    """Document content type constants."""
    PROPERTY = 'property'
    INVESTMENT = 'investment'
    LEGAL = 'legal'
    MARKET = 'market'
    AMENITY = 'amenity'
    ACTIVITY = 'activity'
    RESTAURANT = 'restaurant'
    TOUR = 'tour'
    DEMAND = 'demand'
    PRICING = 'pricing'
    SERVICE = 'service'
    SOP = 'sop'
    VENDOR = 'vendor'
    MAINTENANCE = 'maintenance'
    GUEST = 'guest'
    
    CHOICES = [
        (PROPERTY, _('Property Information')),
        (INVESTMENT, _('Investment Information')),
        (LEGAL, _('Legal Information')),
        (MARKET, _('Market Analysis')),
        (AMENITY, _('Amenity Information')),
        (ACTIVITY, _('Activity Information')),
        (RESTAURANT, _('Restaurant Information')),
        (TOUR, _('Tour Information')),
        (DEMAND, _('Demand Information')),
        (PRICING, _('Pricing Information')),
        (SERVICE, _('Service Information')),
        (SOP, _('Standard Operating Procedure')),
        (VENDOR, _('Vendor Information')),
        (MAINTENANCE, _('Maintenance Information')),
        (GUEST, _('Guest Information')),
    ]


class Document(models.Model):
    """
    Document for RAG knowledge base with vector embeddings.
    Supports role-based access control.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Tenant')
    )
    
    content = models.TextField(
        _('Content'),
        help_text=_('Document text content')
    )
    
    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text=_('Vector embedding for semantic search')
    )
    
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata about this document')
    )
    
    user_roles = ArrayField(
        models.CharField(max_length=20),
        verbose_name=_('Accessible to Roles'),
        help_text=_('Which user roles can access this document')
    )
    
    content_type = models.CharField(
        _('Content Type'),
        max_length=50,
        choices=ContentType.CHOICES,
        help_text=_('Type of content in this document')
    )
    
    freshness_date = models.DateField(
        _('Freshness Date'),
        help_text=_('Date when this information was current')
    )
    
    source_url = models.URLField(
        _('Source URL'),
        max_length=500,
        null=True,
        blank=True,
        help_text=_('Source URL if applicable')
    )
    
    source_reference = models.CharField(
        _('Source Reference'),
        max_length=200,
        blank=True,
        help_text=_('Human-readable source reference')
    )
    
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Is this document active for retrieval?')
    )
    
    times_retrieved = models.IntegerField(
        _('Times Retrieved'),
        default=0,
        help_text=_('How many times this document was retrieved in RAG')
    )
    
    avg_relevance_score = models.DecimalField(
        _('Average Relevance Score'),
        max_digits=4,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=_('Average relevance score when retrieved')
    )
    
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('Updated At'),
        auto_now=True
    )
    
    class Meta:
        db_table = 'documents'
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['content_type', 'is_active']),
            models.Index(fields=['freshness_date']),
            models.Index(fields=['-times_retrieved']),
        ]
    
    def __str__(self):
        return f"{self.get_content_type_display()} - {self.content[:50]}..."
    
    def increment_retrieved(self, relevance_score=None):
        """Increment retrieval count and update average relevance."""
        self.times_retrieved += 1
        
        if relevance_score is not None:
            if self.avg_relevance_score is None:
                self.avg_relevance_score = relevance_score
            else:
                # Running average
                total = self.avg_relevance_score * (self.times_retrieved - 1) + relevance_score
                self.avg_relevance_score = total / self.times_retrieved
        
        self.save(update_fields=['times_retrieved', 'avg_relevance_score'])
    
    def is_fresh(self, max_days=90):
        """Check if document is still fresh."""
        from django.utils import timezone
        from datetime import timedelta
        
        age = (timezone.now().date() - self.freshness_date).days
        return age <= max_days
    
    def can_be_accessed_by(self, user_role):
        """Check if a user role can access this document."""
        return user_role in self.user_roles or 'all' in self.user_roles
