# -*- coding: utf-8 -*-
"""
Direct Database Test (avoiding circular import)
"""

import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from shared_modules.database import DatabaseManager, get_connection
    print("✅ Database module imported successfully")
except Exception as e:
    print(f"❌ Database import failed: {e}")
    exit(1)

def extract_template_keyword(text: str) -> str:
    """Extract keyword category from text"""
    text_lower = text.lower()
    mapping = {
        "생일": "생일/기념일", 
        "기념일": "생일/기념일",
        "축하": "생일/기념일",
        "리뷰": "리뷰 요청", 
        "후기": "리뷰 요청",
        "평가": "리뷰 요청",
        "예약": "예약",
        "설문": "설문 요청",
        "감사": "구매 후 안내", 
        "출고": "구매 후 안내", 
        "배송": "구매 후 안내",
        "발송": "구매 후 안내",
        "재구매": "재구매 유도", 
        "재방문": "재방문",
        "다시": "재구매 유도",
        "VIP": "고객 맞춤 메시지", 
        "맞춤": "고객 맞춤 메시지",
        "특별": "고객 맞춤 메시지",
        "이벤트": "이벤트 안내", 
        "할인": "이벤트 안내", 
        "프로모션": "이벤트 안내",
        "세일": "이벤트 안내"
    }
    
    for keyword, category in mapping.items():
        if keyword in text_lower:
            return category
    return None

def test_database_direct():
    """Test database connection directly"""
    print("=== Direct Database Test ===")
    
    try:
        # Test database connection
        with get_connection() as db:
            print("✅ Database connection: SUCCESS")
            
            # Test basic query
            from sqlalchemy import text
            result = db.execute(text("SELECT COUNT(*) as count FROM template_message"))
            row = result.fetchone()
            total_templates = row[0] if row else 0
            print(f"📊 Total templates in database: {total_templates}")
            
            # Test category-specific query
            result = db.execute(text("""
                SELECT template_type, COUNT(*) as count 
                FROM template_message 
                WHERE user_id = 3 
                GROUP BY template_type
            """))
            
            print("\n📋 Templates by category (user_id=3):")
            for row in result:
                print(f"   • {row[0]}: {row[1]} templates")
            
            # Test keyword detection
            print("\n🔍 Keyword Detection Test:")
            test_messages = [
                "생일 축하 메시지 만들어줘",
                "리뷰 요청하는 방법 알려줘",
                "예약 확인 메시지 보내고 싶어",
                "일반적인 질문입니다"
            ]
            
            for message in test_messages:
                category = extract_template_keyword(message)
                status = category if category else "No match"
                print(f"   📝 '{message}' → {status}")
            
            # Test template existence for specific category
            category = "생일/기념일"
            result = db.execute(text("""
                SELECT title, content
                FROM template_message 
                WHERE template_type = :category AND user_id = 3
                LIMIT 2
            """), {"category": category})
            
            print(f"\n📋 Sample templates for '{category}':")
            templates = result.fetchall()
            if templates:
                for i, template in enumerate(templates, 1):
                    title = template[0]
                    content = template[1][:50] + "..." if len(template[1]) > 50 else template[1]
                    print(f"   {i}. {title}")
                    print(f"      Content: {content}")
            else:
                print(f"   ⚠️ No templates found for '{category}'")
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_save_simulation():
    """Simulate template saving"""
    print("\n=== Template Save Simulation ===")
    
    try:
        with get_connection() as db:
            from sqlalchemy import text
            
            # Check if test user has any templates
            result = db.execute(text("""
                SELECT COUNT(*) as count 
                FROM template_message 
                WHERE user_id = 3
            """))
            
            user_template_count = result.fetchone()[0]
            print(f"📊 User 3 currently has {user_template_count} templates")
            
            # Simulate adding a new template
            category = "생일/기념일"
            print(f"\n🎯 Simulating auto-save for category: '{category}'")
            
            # Get default templates for this category
            result = db.execute(text("""
                SELECT template_id, title, template_type, channel_type, content
                FROM template_message 
                WHERE template_type = :category AND user_id = 3
                LIMIT 2
            """), {"category": category})
            
            default_templates = result.fetchall()
            
            if default_templates:
                print(f"✅ Found {len(default_templates)} default templates")
                for template in default_templates:
                    print(f"   • {template[1]} (ID: {template[0]})")
                    
                # Check if user already has templates of this type
                for template in default_templates:
                    check_result = db.execute(text("""
                        SELECT COUNT(*) as count
                        FROM template_message 
                        WHERE user_id = 3 
                        AND template_type = :template_type 
                        AND channel_type = :channel_type
                    """), {
                        "template_type": template[2],
                        "channel_type": template[3]
                    })
                    
                    existing_count = check_result.fetchone()[0]
                    if existing_count > 0:
                        print(f"   ⚠️ User already has {existing_count} template(s) of type: {template[2]}")
                    else:
                        print(f"   ✅ User doesn't have template of type: {template[2]} - Ready to save!")
            else:
                print(f"❌ No default templates found for '{category}'")
                
    except Exception as e:
        print(f"❌ Template save simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_direct()
    test_template_save_simulation()
    print("\n=== Test Complete ===")
    print("💡 If everything looks good, the auto-save feature should work!")