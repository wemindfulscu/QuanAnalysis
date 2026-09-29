"""
数据库迁移脚本 - 为watchlist表添加last_update字段
"""
import sqlite3
import os

db_path = "data/quant_analysis.db"

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

print(f"连接数据库: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查watchlist表结构
cursor.execute("PRAGMA table_info(watchlist)")
columns = {row[1]: row[2] for row in cursor.fetchall()}
print(f"当前watchlist表字段: {list(columns.keys())}")

# 检查是否已有last_update字段
if 'last_update' not in columns:
    print("\n添加last_update字段...")
    cursor.execute("""
        ALTER TABLE watchlist 
        ADD COLUMN last_update TEXT
    """)
    conn.commit()
    print("✅ 成功添加last_update字段")
else:
    print("⏭️  last_update字段已存在，跳过")

# 显示更新后的表结构
print("\n更新后的watchlist表结构：")
cursor.execute("PRAGMA table_info(watchlist)")
for row in cursor.fetchall():
    print(f"  {row[1]:20} {row[2]:10} {'NOT NULL' if row[3] else ''}")

print("\n✅ 数据库迁移完成")
conn.close()
