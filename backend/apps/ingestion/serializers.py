"""
Serializers for website configuration.
"""

from rest_framework import serializers


class SupportedWebsiteSerializer(serializers.Serializer):
    """Serializer for supported website information."""
    
    id = serializers.CharField(help_text="Website identifier")
    name = serializers.CharField(help_text="Display name")
    url = serializers.URLField(help_text="Website URL")
    color = serializers.CharField(help_text="Brand color")
    active = serializers.BooleanField(help_text="Whether website is active")
    has_extractor = serializers.BooleanField(help_text="Whether site-specific extractor exists")
