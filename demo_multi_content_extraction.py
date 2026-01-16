#!/usr/bin/env python
"""
Demo script showing end-to-end usage of multi-content-type extraction system.
Demonstrates detection and extraction for different content types.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from core.llm.content_detection import detect_content_type
from core.llm.extraction import extract_content_data
from core.llm.content_types import get_content_type_label, get_content_type_icon


# Sample HTML content for different types
SAMPLE_CONTENTS = {
    'real_estate': {
        'url': 'https://www.coldwellbankercostarica.com/property/villa-jaco',
        'html': """
        <html>
            <head><title>Luxury Oceanview Villa for Sale in Jaco</title></head>
            <body>
                <h1>Spectacular 4-Bedroom Villa</h1>
                <div class="property-details">
                    <p><strong>Price:</strong> $650,000 USD</p>
                    <p><strong>Location:</strong> Jaco, Puntarenas Province, Costa Rica</p>
                    <p><strong>Bedrooms:</strong> 4</p>
                    <p><strong>Bathrooms:</strong> 3.5</p>
                    <p><strong>Property Size:</strong> 285 m² (3,068 sqft)</p>
                    <p><strong>Lot Size:</strong> 800 m²</p>
                    <p><strong>Property Type:</strong> Villa</p>
                    <p><strong>Listing ID:</strong> CB-12345</p>
                    <div class="description">
                        This stunning modern villa offers breathtaking ocean views from every room.
                        Features include infinity pool, gourmet kitchen, marble floors, and smart home technology.
                        Located in exclusive gated community with 24/7 security, just 10 minutes from the beach.
                    </div>
                    <div class="amenities">
                        <h3>Amenities:</h3>
                        <ul>
                            <li>Infinity Pool</li>
                            <li>Gourmet Kitchen</li>
                            <li>Ocean View</li>
                            <li>24/7 Security</li>
                            <li>Smart Home</li>
                            <li>2-Car Garage</li>
                        </ul>
                    </div>
                </div>
            </body>
        </html>
        """
    },
    'tour': {
        'url': 'https://www.viator.com/tours/costa-rica/zipline-canopy-adventure',
        'html': """
        <html>
            <head><title>Rainforest Zipline Canopy Adventure Tour</title></head>
            <body>
                <h1>Ultimate Zipline Canopy Tour</h1>
                <div class="tour-details">
                    <p><strong>Price:</strong> $95 per person</p>
                    <p><strong>Duration:</strong> 4 hours</p>
                    <p><strong>Difficulty:</strong> Moderate</p>
                    <p><strong>Type:</strong> Adventure & Wildlife</p>
                    <p><strong>Location:</strong> Monteverde Cloud Forest</p>
                    <p><strong>Min Age:</strong> 10 years</p>
                    <p><strong>Max Group:</strong> 15 participants</p>
                    
                    <div class="description">
                        Soar through the rainforest canopy on 12 ziplines spanning over 2 miles!
                        Experience breathtaking views while spotting monkeys, sloths, and tropical birds.
                        Professional bilingual guides ensure your safety and provide fascinating insights
                        about the cloud forest ecosystem.
                    </div>
                    
                    <h3>What's Included:</h3>
                    <ul>
                        <li>Hotel pickup and drop-off</li>
                        <li>Professional guide (English/Spanish)</li>
                        <li>All safety equipment</li>
                        <li>Light snacks and water</li>
                        <li>Rainforest hike</li>
                        <li>Photos and videos</li>
                    </ul>
                    
                    <h3>What to Bring:</h3>
                    <ul>
                        <li>Closed-toe shoes</li>
                        <li>Sunscreen</li>
                        <li>Camera</li>
                        <li>Light jacket</li>
                    </ul>
                    
                    <p><strong>Cancellation Policy:</strong> Free cancellation up to 24 hours before</p>
                </div>
            </body>
        </html>
        """
    },
    'restaurant': {
        'url': 'https://www.tripadvisor.com/restaurant/el-pescador-jaco',
        'html': """
        <html>
            <head><title>El Pescador Seafood Restaurant - Jaco</title></head>
            <body>
                <h1>El Pescador - Fresh Seafood & Ocean Views</h1>
                <div class="restaurant-info">
                    <p><strong>Cuisine:</strong> Seafood, Costa Rican, International</p>
                    <p><strong>Price Range:</strong> $$ - $$$ (Moderate to Upscale)</p>
                    <p><strong>Average:</strong> $35-50 per person</p>
                    <p><strong>Location:</strong> Beachfront, Jaco Centro</p>
                    <p><strong>Hours:</strong> Daily 11:00 AM - 10:00 PM</p>
                    <p><strong>Reservations:</strong> Recommended for dinner</p>
                    <p><strong>Phone:</strong> +506 2643-3982</p>
                    
                    <div class="description">
                        Experience the freshest seafood in Jaco with stunning sunset views.
                        Our chef sources daily catches directly from local fishermen.
                        Romantic beachfront setting perfect for special occasions.
                    </div>
                    
                    <h3>Signature Dishes:</h3>
                    <ul>
                        <li>Grilled Mahi-Mahi with tropical salsa</li>
                        <li>Traditional Costa Rican ceviche</li>
                        <li>Lobster thermidor</li>
                        <li>Seafood paella for two</li>
                        <li>Catch of the day (grilled or pan-seared)</li>
                        <li>Coconut shrimp</li>
                    </ul>
                    
                    <h3>Atmosphere:</h3>
                    <p>Romantic beachfront dining with live music on weekends</p>
                    
                    <h3>Dietary Options:</h3>
                    <ul>
                        <li>Vegetarian options available</li>
                        <li>Gluten-free options available</li>
                        <li>Fresh fruit and salads</li>
                    </ul>
                    
                    <p><strong>Dress Code:</strong> Smart casual</p>
                </div>
            </body>
        </html>
        """
    },
}


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_header(title):
    """Print formatted section header."""
    print("\n")
    print_separator("=")
    print(f" {title}")
    print_separator("=")
    print()


def demo_detection_and_extraction(content_type_key):
    """Demo the full flow for a content type."""
    sample = SAMPLE_CONTENTS[content_type_key]
    url = sample['url']
    html = sample['html']
    
    print_header(f"DEMO: {content_type_key.upper()}")
    
    print(f"📄 URL: {url}\n")
    
    # Step 1: Detection
    print("🔍 STEP 1: DETECTING CONTENT TYPE")
    print_separator("-")
    
    detection = detect_content_type(
        url=url,
        html=html,
        use_llm_fallback=False
    )
    
    icon = get_content_type_icon(detection['content_type'])
    label = get_content_type_label(detection['content_type'])
    
    print(f"✅ Detected Type: {icon} {label}")
    print(f"   Confidence: {detection['confidence']:.1%}")
    print(f"   Method: {detection['method']}")
    print()
    
    # Step 2: Extraction
    print("🤖 STEP 2: EXTRACTING DATA WITH LLM")
    print_separator("-")
    print("⏳ Processing with OpenAI (this may take a few seconds)...\n")
    
    try:
        extracted_data = extract_content_data(
            content=html,
            content_type=detection['content_type'],
            url=url
        )
        
        # Step 3: Display results
        print("✅ EXTRACTION COMPLETE!")
        print()
        print("📊 EXTRACTED DATA:")
        print_separator("-")
        
        # Display key fields based on content type
        if content_type_key == 'real_estate':
            print(f"  Property Name: {extracted_data.get('property_name')}")
            print(f"  Price: ${extracted_data.get('price_usd'):,.0f}" if extracted_data.get('price_usd') else "  Price: N/A")
            print(f"  Location: {extracted_data.get('location')}")
            print(f"  Bedrooms: {extracted_data.get('bedrooms')}")
            print(f"  Bathrooms: {extracted_data.get('bathrooms')}")
            print(f"  Size: {extracted_data.get('square_meters')} m²")
            print(f"  Property Type: {extracted_data.get('property_type')}")
            
        elif content_type_key == 'tour':
            print(f"  Tour Name: {extracted_data.get('tour_name')}")
            print(f"  Price: ${extracted_data.get('price_usd')}" if extracted_data.get('price_usd') else "  Price: N/A")
            print(f"  Duration: {extracted_data.get('duration_hours')} hours")
            print(f"  Difficulty: {extracted_data.get('difficulty_level')}")
            print(f"  Location: {extracted_data.get('location')}")
            print(f"  Max Participants: {extracted_data.get('max_participants')}")
            if extracted_data.get('included_items'):
                print(f"  Includes: {', '.join(extracted_data['included_items'][:3])}...")
                
        elif content_type_key == 'restaurant':
            print(f"  Restaurant: {extracted_data.get('restaurant_name')}")
            print(f"  Cuisine: {extracted_data.get('cuisine_type')}")
            print(f"  Price Range: {extracted_data.get('price_range')}")
            print(f"  Avg Price: ${extracted_data.get('average_price_per_person')}" if extracted_data.get('average_price_per_person') else "")
            print(f"  Location: {extracted_data.get('location')}")
            print(f"  Hours: {extracted_data.get('hours_of_operation')}")
            if extracted_data.get('signature_dishes'):
                print(f"  Signature Dishes: {', '.join(extracted_data['signature_dishes'][:3])}")
        
        print()
        print(f"  Confidence: {extracted_data.get('extraction_confidence', 0):.1%}")
        print(f"  Reasoning: {extracted_data.get('confidence_reasoning', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run the demo."""
    print("\n")
    print_separator("=")
    print(" 🎭 MULTI-CONTENT-TYPE EXTRACTION DEMO")
    print_separator("=")
    print()
    print("This demo shows the complete flow:")
    print("  1. Content type detection (domain + keywords)")
    print("  2. Data extraction with specialized prompts")
    print("  3. Structured output for each content type")
    print()
    input("Press ENTER to start the demo...")
    
    # Demo each content type
    for content_type in ['real_estate', 'tour', 'restaurant']:
        demo_detection_and_extraction(content_type)
        
        if content_type != 'restaurant':  # Not last item
            print()
            input("Press ENTER to continue to next demo...")
    
    print()
    print_separator("=")
    print("✅ DEMO COMPLETE!")
    print_separator("=")
    print()
    print("💡 Key Takeaways:")
    print("  • Detection is fast and accurate (domain + keywords)")
    print("  • Each content type uses a specialized prompt")
    print("  • Extracted data structure matches the content type")
    print("  • System is extensible (easy to add new types)")
    print()
    print("📖 For more info, see: documentation/MULTI_CONTENT_TYPE_SYSTEM.md")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
