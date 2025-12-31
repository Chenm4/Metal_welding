import json
import pymysql
from pathlib import Path
import sys

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

def cleanup_metadata():
    config_path = Path('backend/config/dataset_metadata.json')
    if not config_path.exists():
        print("Metadata file not found.")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    conn = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        existing_tables = [list(row.values())[0] for row in cursor.fetchall()]
        print(f"Existing tables in DB: {existing_tables}")

        new_datasets = {}
        for dataset_id, config in metadata['datasets'].items():
            table_name = config['table_name']
            if table_name in existing_tables:
                new_datasets[dataset_id] = config
                print(f"Keeping dataset: {dataset_id} (table: {table_name})")
            else:
                print(f"Removing stale dataset: {dataset_id} (table: {table_name} not found)")

        metadata['datasets'] = new_datasets

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print("Cleanup complete.")

    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_metadata()
