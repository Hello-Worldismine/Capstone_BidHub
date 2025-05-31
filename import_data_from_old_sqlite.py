import sqlite3
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

def import_specific_tables(source_db_path, tables_list):
    """특정 테이블들만 가져오는 함수"""
    
    if not os.path.exists(source_db_path):
        print(f"❌ Source database not found: {source_db_path}")
        return
    
    print(f"📁 Source DB: {source_db_path}")
    print(f"📋 Tables to import: {', '.join(tables_list)}")
    
    # 소스 데이터베이스 연결
    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    
    try:
        # 소스 DB의 테이블 목록 확인
        cursor = source_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        available_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Available tables: {', '.join(available_tables)}")
        
        # 존재하는 테이블만 필터링
        valid_tables = [table for table in tables_list if table in available_tables]
        missing_tables = [table for table in tables_list if table not in available_tables]
        
        if missing_tables:
            print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
        
        if not valid_tables:
            print("❌ No valid tables to import")
            return
        
        for table in valid_tables:
            import_single_table(source_conn, table)
            
        print("\n✅ Import completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        source_conn.close()

def import_single_table(source_conn, table_name):
    """단일 테이블 임포트"""
    print(f"\n📋 Processing: {table_name}")
    
    try:
        # 소스 데이터 확인
        cursor = source_conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        if row_count == 0:
            print(f"  ⚠️  No data in {table_name}")
            return
        
        print(f"  📊 Found {row_count} rows")
        
        # 기존 데이터 삭제 (선택사항)
        confirm = input(f"  🗑️  Clear existing data in {table_name}? (y/N): ")
        if confirm.lower() == 'y':
            with connection.cursor() as django_cursor:
                django_cursor.execute(f"DELETE FROM {table_name}")
                print(f"  ✅ Cleared existing data")
        
        # 데이터 가져오기
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"  ⚠️  No data to import")
            return
        
        # 컬럼 정보 가져오기
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Django DB에 삽입
        with connection.cursor() as django_cursor:
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # 배치 처리
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                batch_data = [list(row) for row in batch]
                django_cursor.executemany(insert_query, batch_data)
                
                print(f"  📥 Inserted {min(i + batch_size, len(rows))}/{len(rows)} rows")
        
        print(f"  ✅ Successfully imported {len(rows)} rows")
        
    except Exception as e:
        print(f"  ❌ Failed to import {table_name}: {e}")

if __name__ == "__main__":
    # 사용 설정
    source_database = input("Source database path: ").strip() or "old_db.sqlite3"
    
    # 기본 테이블 목록
    default_tables = [
        'auction_case',
        'auction_item', 
        'auction_schedule',
        'property_listing',
        'claim_distribution',
        'auction_party'
    ]
    
    print(f"Default tables: {', '.join(default_tables)}")
    custom_tables = input("Enter custom tables (comma-separated) or press Enter for default: ").strip()
    
    if custom_tables:
        tables_to_import = [table.strip() for table in custom_tables.split(',')]
    else:
        tables_to_import = default_tables
    
    import_specific_tables(source_database, tables_to_import)