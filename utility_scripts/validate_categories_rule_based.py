"""
Smart Rule-Based Category Validator
No API needed - uses keywords and patterns to validate travel place categories
"""

import csv
import re
from collections import defaultdict

class CategoryValidator:
    
    # Keywords for activities
    RESTAURANT_KEYWORDS = [
        'restaurant', 'cafe', 'coffee', 'sushi', 'ramen', 'bar', 'grill',
        'kitchen', 'dining', 'bistro', 'eatery', 'diner', 'pizzeria', 'bakery',
        'レストラン', '食堂', '居酒屋', 'カフェ', '喫茶', 'ベーカリー'
    ]
    
    TEMPLE_KEYWORDS = [
        'temple', 'shrine', 'jinja', 'tera', 'ji', 'taisha', 'gokoku',
        '寺', '神社', '大社', '宮', '院', 'buddhist', 'shinto'
    ]
    
    PARK_KEYWORDS = [
        'park', 'garden', 'koen', '公園', '庭園', 'arboretum', 'botanical'
    ]
    
    MUSEUM_KEYWORDS = [
        'museum', 'gallery', 'hakubutsukan', 'aquarium', 'zoo',
        '博物館', '美術館', '資料館', '記念館', '水族館', 'memorial hall'
    ]
    
    SHOPPING_KEYWORDS = [
        'shop', 'store', 'market', 'mall', 'boutique', 'mart',
        '店', 'ショップ', 'ストア', '市場', 'マート', '商店'
    ]
    
    HOTEL_KEYWORDS = [
        'hotel', 'inn', 'resort', 'ryokan', 'hostel', 'lodge', 'guesthouse',
        'ホテル', '旅館', '宿', 'リゾート', 'ゲストハウス'
    ]
    
    TRANSPORT_KEYWORDS = [
        'station', 'airport', 'terminal', 'bus', 'train', 'port', 'ferry',
        '駅', '空港', 'ターミナル', 'バス', '鉄道', 'ferry terminal'
    ]
    
    # Keywords for cuisines
    SUSHI_KEYWORDS = ['sushi', 'すし', '寿司', '鮨']
    RAMEN_KEYWORDS = ['ramen', 'らーめん', 'ラーメン', '拉麺', 'noodle']
    CAFE_KEYWORDS = ['cafe', 'coffee', 'カフェ', '喫茶', 'コーヒー', 'caffè']
    TEMPURA_KEYWORDS = ['tempura', '天ぷら', '天麩羅']
    IZAKAYA_KEYWORDS = ['izakaya', '居酒屋']
    YAKITORI_KEYWORDS = ['yakitori', '焼き鳥', '焼鳥']
    DESSERT_KEYWORDS = ['dessert', 'sweets', 'cake', 'bakery', 'patisserie', 
                        'スイーツ', 'ケーキ', 'パティスリー', 'ベーカリー',
                        'gelato', 'ice cream', 'pastry', 'scone']
    JAPANESE_KEYWORDS = ['japanese', 'nihon', 'washoku', '和食']
    ITALIAN_KEYWORDS = ['italian', 'イタリアン', 'trattoria', 'osteria', 'pizza']
    CHINESE_KEYWORDS = ['chinese', '中華', 'dim sum']
    KOREAN_KEYWORDS = ['korean', '韓国', 'bbq']
    
    def check_activity(self, place_name, current_activity):
        """Suggest activity based on name"""
        name_lower = place_name.lower()
        suggestions = []
        
        # Check each category (order matters - more specific first)
        if any(kw in name_lower or kw in place_name for kw in self.TEMPLE_KEYWORDS):
            suggestions.append(('temple', 'high'))
        
        if any(kw in name_lower or kw in place_name for kw in self.TRANSPORT_KEYWORDS):
            suggestions.append(('transport', 'high'))
        
        if any(kw in name_lower or kw in place_name for kw in self.MUSEUM_KEYWORDS):
            suggestions.append(('museum', 'high'))
        
        if any(kw in name_lower or kw in place_name for kw in self.PARK_KEYWORDS):
            suggestions.append(('park', 'high'))
        
        if any(kw in name_lower or kw in place_name for kw in self.HOTEL_KEYWORDS):
            suggestions.append(('hotel', 'high'))
        
        if any(kw in name_lower or kw in place_name for kw in self.RESTAURANT_KEYWORDS):
            suggestions.append(('restaurant', 'high'))
        
        if any(kw in name_lower or kw in place_name for kw in self.SHOPPING_KEYWORDS):
            suggestions.append(('shopping', 'medium'))
        
        if suggestions:
            # Return first (highest priority) suggestion
            return suggestions[0][0], suggestions[0][1]
        
        return None, 'none'
    
    def check_cuisine(self, place_name, current_activity):
        """Suggest cuisine based on name"""
        name_lower = place_name.lower()
        
        # Only suggest cuisine if it's a restaurant
        if current_activity not in ['restaurant', '']:
            return None, 'none'
        
        if any(kw in name_lower or kw in place_name for kw in self.SUSHI_KEYWORDS):
            return 'sushi', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.RAMEN_KEYWORDS):
            return 'ramen', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.CAFE_KEYWORDS):
            return 'cafe', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.TEMPURA_KEYWORDS):
            return 'tempura', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.IZAKAYA_KEYWORDS):
            return 'izakaya', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.YAKITORI_KEYWORDS):
            return 'yakitori', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.DESSERT_KEYWORDS):
            return 'dessert', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.ITALIAN_KEYWORDS):
            return 'italian', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.CHINESE_KEYWORDS):
            return 'chinese', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.KOREAN_KEYWORDS):
            return 'korean', 'high'
        
        if any(kw in name_lower or kw in place_name for kw in self.JAPANESE_KEYWORDS):
            return 'japanese', 'medium'
        
        return None, 'none'

def validate_travel_places(input_file='seed-data/travel_places.csv', 
                          output_file='validation_results.csv'):
    """Validate travel places CSV"""
    
    validator = CategoryValidator()
    issues = []
    stats = {
        'total': 0,
        'activity_mismatches': 0,
        'cuisine_suggestions': 0,
        'empty_activities': 0,
        'empty_cuisines': 0,
        'high_confidence_errors': 0,
        'medium_confidence_errors': 0
    }
    
    print("=" * 70)
    print("RULE-BASED CATEGORY VALIDATOR")
    print("=" * 70)
    print(f"\nReading: {input_file}")
    print("Processing...\n")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):
            stats['total'] += 1
            place_name = row['place_name']
            current_activity = row.get('activities', '').strip()
            current_cuisine = row.get('cuisines', '').strip()
            prefecture = row.get('prefecture', '')
            
            # Track empty fields
            if not current_activity:
                stats['empty_activities'] += 1
            if not current_cuisine:
                stats['empty_cuisines'] += 1
            
            # Check activity
            suggested_activity, activity_confidence = validator.check_activity(
                place_name, current_activity
            )
            
            # Check cuisine
            suggested_cuisine, cuisine_confidence = validator.check_cuisine(
                place_name, current_activity
            )
            
            # Flag mismatches
            issue = {
                'row': row_num,
                'place_name': place_name,
                'prefecture': prefecture,
                'current_activity': current_activity,
                'suggested_activity': suggested_activity or '',
                'activity_confidence': activity_confidence,
                'current_cuisine': current_cuisine,
                'suggested_cuisine': suggested_cuisine or '',
                'cuisine_confidence': cuisine_confidence,
                'issue_type': []
            }
            
            has_issue = False
            
            # Activity mismatch
            if suggested_activity and current_activity != suggested_activity:
                stats['activity_mismatches'] += 1
                issue['issue_type'].append(f"Activity mismatch ({activity_confidence} confidence)")
                has_issue = True
                
                if activity_confidence == 'high':
                    stats['high_confidence_errors'] += 1
                elif activity_confidence == 'medium':
                    stats['medium_confidence_errors'] += 1
            
            # Missing or different cuisine
            if suggested_cuisine and (not current_cuisine or current_cuisine != suggested_cuisine):
                if not current_cuisine:
                    issue['issue_type'].append(f"Missing cuisine ({cuisine_confidence} confidence)")
                else:
                    issue['issue_type'].append(f"Cuisine mismatch ({cuisine_confidence} confidence)")
                stats['cuisine_suggestions'] += 1
                has_issue = True
            
            if has_issue:
                issue['issue_type'] = ' | '.join(issue['issue_type'])
                issues.append(issue)
    
    # Write issues to CSV
    if issues:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['row', 'place_name', 'prefecture', 'current_activity', 
                         'suggested_activity', 'activity_confidence', 'current_cuisine', 
                         'suggested_cuisine', 'cuisine_confidence', 'issue_type']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(issues)
    
    # Print summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total places validated: {stats['total']}")
    print(f"\n📊 Issues Found:")
    print(f"  ⚠️  Activity mismatches: {stats['activity_mismatches']}")
    print(f"      - High confidence: {stats['high_confidence_errors']}")
    print(f"      - Medium confidence: {stats['medium_confidence_errors']}")
    print(f"  💡 Cuisine suggestions: {stats['cuisine_suggestions']}")
    print(f"\n📝 Empty Fields:")
    print(f"  Empty activities: {stats['empty_activities']} ({stats['empty_activities']/stats['total']*100:.1f}%)")
    print(f"  Empty cuisines: {stats['empty_cuisines']} ({stats['empty_cuisines']/stats['total']*100:.1f}%)")
    
    if issues:
        print(f"\n📄 Detailed report saved to: {output_file}")
        print(f"   Total issues found: {len(issues)}")
        
        # Separate by confidence
        high_conf = [i for i in issues if 'high confidence' in i['issue_type'].lower()]
        medium_conf = [i for i in issues if 'medium confidence' in i['issue_type'].lower()]
        
        print(f"\n{'='*70}")
        print("TOP 15 HIGH-CONFIDENCE ISSUES (Should fix these first!)")
        print(f"{'='*70}")
        for issue in high_conf[:15]:
            print(f"\n  Row {issue['row']}: {issue['place_name']} ({issue['prefecture']})")
            if issue['suggested_activity'] and issue['suggested_activity'] != issue['current_activity']:
                print(f"    ❌ Activity: '{issue['current_activity']}' → ✅ '{issue['suggested_activity']}'")
            if issue['suggested_cuisine'] and issue['suggested_cuisine'] != issue['current_cuisine']:
                print(f"    ❌ Cuisine: '{issue['current_cuisine']}' → ✅ '{issue['suggested_cuisine']}'")
        
        if len(high_conf) > 15:
            print(f"\n  ... and {len(high_conf) - 15} more high-confidence issues (see CSV)")
        
        print(f"\n{'='*70}")
        print("NEXT STEPS:")
        print(f"{'='*70}")
        print(f"1. Review the {len(high_conf)} high-confidence issues above")
        print(f"2. Open '{output_file}' to see all issues")
        print(f"3. Fix obvious errors manually or run OpenAI validator on uncertain cases")
        print(f"4. For OpenAI validation of remaining issues, run:")
        print(f"   .\.venv\Scripts\python.exe utility_scripts/validate_with_openai.py")
    else:
        print(f"\n✅ No issues found! Your data looks good.")
    
    print(f"\n{'='*70}\n")
    return issues, stats

if __name__ == '__main__':
    issues, stats = validate_travel_places()

