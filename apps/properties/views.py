"""
Views for Properties API.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Property
from .serializers import (
    PropertyListSerializer,
    PropertyDetailSerializer,
    PropertyCreateSerializer,
    PropertyVerifySerializer
)


class PropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Property management.
    Supports filtering, searching, and role-based access.
    """
    
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'property_type', 'location', 'source_website']
    search_fields = ['property_name', 'description', 'location']
    ordering_fields = ['created_at', 'price_usd', 'property_name', 'source_website']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return all active properties."""
        queryset = Property.objects.filter(
            is_active=True
        ).select_related('tenant', 'verified_by').prefetch_related('images')
        
        # Query params filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        bedrooms = self.request.query_params.get('bedrooms')
        
        if min_price:
            queryset = queryset.filter(price_usd__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_usd__lte=max_price)
        if bedrooms:
            queryset = queryset.filter(bedrooms=bedrooms)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return PropertyListSerializer
        elif self.action == 'create':
            return PropertyCreateSerializer
        elif self.action == 'verify':
            return PropertyVerifySerializer
        return PropertyDetailSerializer
    
    def perform_create(self, serializer):
        """Set tenant and extraction timestamp on create."""
        serializer.save(
            tenant=self.request.user.tenant,
            extracted_at=timezone.now()
        )
    
    @action(detail=True, methods=['patch'], url_path='verify')
    def verify(self, request, pk=None):
        """Mark property as manually verified."""
        property_obj = self.get_object()
        serializer = PropertyVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            if serializer.validated_data['verified']:
                property_obj.last_verified = timezone.now()
                property_obj.verified_by = request.user
                property_obj.save(update_fields=['last_verified', 'verified_by'])
                
                return Response({
                    'status': 'success',
                    'message': 'Property marked as verified',
                    'verified_at': property_obj.last_verified
                })
            else:
                return Response({
                    'status': 'info',
                    'message': 'Property verification removed'
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get property statistics for current tenant."""
        queryset = self.get_queryset()
        
        from django.db.models import Count, Avg, Min, Max
        
        stats = queryset.aggregate(
            total=Count('id'),
            avg_price=Avg('price_usd'),
            min_price=Min('price_usd'),
            max_price=Max('price_usd')
        )
        
        by_status = queryset.values('status').annotate(count=Count('id'))
        by_type = queryset.values('property_type').annotate(count=Count('id'))
        
        return Response({
            'overview': stats,
            'by_status': list(by_status),
            'by_type': list(by_type)
        })
