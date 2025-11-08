"""
OpenAI-Powered Category Validator and Data Populator
Validates existing categories and fills in missing data for travel places
Uses gpt-4o-mini for cost-effective processing
"""

import csv
import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Valid categories
VALID_ACTIVITIES = ['temple', 'restaurant', 'park', 'museum', 'shopping', 
                    'transport', 'hotel', 'entertainment', 'nature', 'historical']

VALID_CUISINES = ['cafe', 'sushi', 'ramen', 'japanese', 'dessert', 'tempura', 
                  'chinese', 'izakaya', 'italian', 'yakitori', 'western', 'korean']

def validate_batch_with_openai(places_batch, batch_num, total_batches):
    """Validate and populate a batch of places with OpenAI"""
    
    places_list = []
    for i, place in enumerate(places_batch):
        place_info = f"{i+1}. Name: '{place['name']}'"
        if place['activity']:
            place_info += f" | Current activity: {place['activity']}"
        if place['cuisine']:
            place_info += f" | Current cuisine: {place['cuisine']}"
        places_list.append(place_info)
    
    places_text = "\n".join(places_list)
    
    prompt = f"""You are a Japan travel data expert. Analyze these places and provide the correct activity and cuisine categories.

VALID ACTIVITIES: {', '.join(VALID_ACTIVITIES)}
VALID CUISINES (only for restaurants): {', '.join(VALID_CUISINES)}

RULES:
1. Choose ONE activity from the valid list
2. Only suggest cuisine if activity is "restaurant"
3. If current data is correct, keep it
4. Use empty string "" if no cuisine applies (non-restaurants)
5. Be specific - "cafe" over "japanese", "sushi" over "japanese" when applicable

Places to analyze (batch {batch_num}/{total_batches}):
{places_text}

Return ONLY valid JSON array (no markdown, no explanation):
[{{"index": 1, "activity": "temple", "cuisine": "", "confidence": "high"}}, ...]

Confidence levels: high (99% sure), medium (80% sure), low (60% sure)"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        results = json.loads(result_text)
        return results
        
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON parsing error in batch {batch_num}: {e}")
        print(f"  Response was: {result_text[:200]}...")
        return []
    except Exception as e:
        print(f"  ❌ Error in batch {batch_num}: {e}")
        return []

def validate_and_populate(input_file='seed-data/travel_places.csv',
                         output_file='seed-data/travel_places_validated.csv',
                         report_file='validation_changes_report.csv',
                         batch_size=20,
                         max_places=None,
                         dry_run=False):
    """
    Main validation and population function
    
    Args:
        input_file: Input CSV file
        output_file: Output CSV file with corrections
        report_file: CSV report of all changes
        batch_size: Number of places to process per API call
        max_places: Limit number of places (None = all)
        dry_run: If True, estimate cost without making API calls
    """
    
    print("=" * 70)
    print("OPENAI CATEGORY VALIDATOR & DATA POPULATOR")
    print("=" * 70)
    
    # Read all places
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        all_rows = list(reader)
    
    total_places = len(all_rows)
    if max_places:
        all_rows = all_rows[:max_places]
        total_places = max_places
    
    # Calculate cost estimate
    estimated_cost = (total_places / batch_size) * 0.001  # ~$0.001 per batch
    
    print(f"\n📊 Processing Summary:")
    print(f"  Total places: {total_places}")
    print(f"  Batch size: {batch_size} places")
    print(f"  Total batches: {(total_places + batch_size - 1) // batch_size}")
    print(f"  Estimated cost: ${estimated_cost:.2f}")
    print(f"  Model: gpt-4o-mini")
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No API calls will be made")
        return
    
    # Confirm to proceed
    print(f"\n⚠️  This will use OpenAI API and cost approximately ${estimated_cost:.2f}")
    response = input("Proceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    print(f"\n🚀 Starting validation...\n")
    
    changes = []
    stats = {
        'total': 0,
        'activities_added': 0,
        'activities_changed': 0,
        'cuisines_added': 0,
        'cuisines_changed': 0,
        'no_change': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0
    }
    
    # Process in batches
    for batch_start in range(0, len(all_rows), batch_size):
        batch_end = min(batch_start + batch_size, len(all_rows))
        batch = all_rows[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (len(all_rows) + batch_size - 1) // batch_size
        
        # Prepare batch data
        places_batch = []
        for row in batch:
            places_batch.append({
                'name': row['place_name'],
                'activity': row.get('activities', '').strip(),
                'cuisine': row.get('cuisines', '').strip(),
                'row_num': batch_start + len(places_batch) + 2  # +2 for header and 0-indexing
            })
        
        print(f"Processing batch {batch_num}/{total_batches} (rows {batch_start+2}-{batch_end+1})...", end=' ')
        
        # Get OpenAI suggestions
        results = validate_batch_with_openai(places_batch, batch_num, total_batches)
        
        if not results:
            print("❌ Failed")
            continue
        
        print("✅")
        
        # Apply results
        for result in results:
            idx = result.get('index', 0) - 1
            if idx < 0 or idx >= len(batch):
                continue
            
            row = batch[idx]
            place = places_batch[idx]
            stats['total'] += 1
            
            suggested_activity = result.get('activity', '').strip()
            suggested_cuisine = result.get('cuisine', '').strip()
            confidence = result.get('confidence', 'medium')
            
            # Track confidence
            stats[f'{confidence}_confidence'] += 1
            
            # Check for changes
            current_activity = row.get('activities', '').strip()
            current_cuisine = row.get('cuisines', '').strip()
            
            change_record = {
                'row': place['row_num'],
                'place_name': place['name'],
                'old_activity': current_activity,
                'new_activity': suggested_activity,
                'old_cuisine': current_cuisine,
                'new_cuisine': suggested_cuisine,
                'confidence': confidence,
                'change_type': []
            }
            
            has_change = False
            
            # Activity changes
            if not current_activity and suggested_activity:
                stats['activities_added'] += 1
                change_record['change_type'].append('Activity added')
                row['activities'] = suggested_activity
                has_change = True
            elif current_activity and suggested_activity and current_activity != suggested_activity:
                stats['activities_changed'] += 1
                change_record['change_type'].append('Activity changed')
                row['activities'] = suggested_activity
                has_change = True
            
            # Cuisine changes
            if not current_cuisine and suggested_cuisine:
                stats['cuisines_added'] += 1
                change_record['change_type'].append('Cuisine added')
                row['cuisines'] = suggested_cuisine
                has_change = True
            elif current_cuisine and suggested_cuisine and current_cuisine != suggested_cuisine:
                stats['cuisines_changed'] += 1
                change_record['change_type'].append('Cuisine changed')
                row['cuisines'] = suggested_cuisine
                has_change = True
            
            if has_change:
                change_record['change_type'] = ' | '.join(change_record['change_type'])
                changes.append(change_record)
            else:
                stats['no_change'] += 1
        
        # Rate limiting - be nice to OpenAI
        time.sleep(0.5)
    
    # Write updated CSV
    print(f"\n💾 Writing updated data to: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    # Write changes report
    if changes:
        print(f"📄 Writing changes report to: {report_file}")
        with open(report_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'row', 'place_name', 'old_activity', 'new_activity',
                'old_cuisine', 'new_cuisine', 'confidence', 'change_type'
            ])
            writer.writeheader()
            writer.writerows(changes)
    
    # Print summary
    print(f"\n{'='*70}")
    print("VALIDATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n📊 Results:")
    print(f"  Total places processed: {stats['total']}")
    print(f"  No changes needed: {stats['no_change']}")
    print(f"\n✏️  Changes Made:")
    print(f"  Activities added: {stats['activities_added']}")
    print(f"  Activities changed: {stats['activities_changed']}")
    print(f"  Cuisines added: {stats['cuisines_added']}")
    print(f"  Cuisines changed: {stats['cuisines_changed']}")
    print(f"\n📈 Confidence Distribution:")
    print(f"  High confidence: {stats['high_confidence']}")
    print(f"  Medium confidence: {stats['medium_confidence']}")
    print(f"  Low confidence: {stats['low_confidence']}")
    print(f"\n📁 Output Files:")
    print(f"  ✅ Updated data: {output_file}")
    print(f"  ✅ Changes report: {report_file}")
    
    if changes:
        print(f"\n{'='*70}")
        print("SAMPLE CHANGES (First 10):")
        print(f"{'='*70}")
        for change in changes[:10]:
            print(f"\n  Row {change['row']}: {change['place_name']}")
            if 'Activity' in change['change_type']:
                print(f"    Activity: '{change['old_activity']}' → '{change['new_activity']}'")
            if 'Cuisine' in change['change_type']:
                print(f"    Cuisine: '{change['old_cuisine']}' → '{change['new_cuisine']}'")
            print(f"    Confidence: {change['confidence']}")
    
    print(f"\n{'='*70}")
    print("✨ NEXT STEPS:")
    print(f"{'='*70}")
    print(f"1. Review the changes report: {report_file}")
    print(f"2. If satisfied, replace your original file:")
    print(f"   copy {output_file} seed-data\\travel_places.csv")
    print(f"3. Re-import to Neo4j database if needed")
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    import sys
    
    # Check if dry-run argument provided
    dry_run = '--dry-run' in sys.argv
    
    # Process all places
    validate_and_populate(
        input_file='seed-data/travel_places.csv',
        output_file='seed-data/travel_places_validated.csv',
        report_file='validation_changes_report.csv',
        batch_size=20,  # 20 places per API call
        max_places=None,  # None = process all places
        dry_run=dry_run  # Set to True to see cost estimate without API calls
    )

