"""
数据库迁移脚本 - 更新monitor_tasks表结构
添加update_schedule（数据更新时间）和scan_schedule（信号扫描时间）字段
"""
import sqlite3
import os
from datetime import datetime

db_path = "data/quant_analysis.db"

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

print(f"连接数据库: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查monitor_tasks表是否存在
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='monitor_tasks'
""")
table_exists = cursor.fetchone() is not None

if not table_exists:
    print("monitor_tasks表不存在，创建新表...")
    cursor.execute("""
        CREATE TABLE monitor_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            task_name TEXT NOT NULL,
            email TEXT NOT NULL,
            update_schedule TEXT DEFAULT '09:30',
            scan_schedule TEXT DEFAULT '15:30',
            strategy TEXT DEFAULT 'default',
            remark TEXT,
            enabled INTEGER DEFAULT 1,
            last_update TEXT,
            last_scan TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    print("✅ 创建monitor_tasks表成功")
else:
    print("monitor_tasks表已存在，检查字段...")
    
    # 获取现有字段
    cursor.execute("PRAGMA table_info(monitor_tasks)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"现有字段: {list(columns.keys())}")
    
    # 需要添加的新字段
    new_fields = {
        'update_schedule': "TEXT DEFAULT '09:30'",
        'scan_schedule': "TEXT DEFAULT '15:30'",
        'strategy': "TEXT DEFAULT 'default'",
        'remark': "TEXT",
        'last_update': "TEXT",
        'last_scan': "TEXT"
    }
    
    # 添加缺失的字段
    for field_name, field_type in new_fields.items():
        if field_name not in columns:
            print(f"添加字段: {field_name}")
            cursor.execute(f"ALTER TABLE monitor_tasks ADD COLUMN {field_name} {field_type}")
            conn.commit()
            print(f"✅ 添加字段 {field_name} 成功")
        else:
            print(f"⏭️  字段 {field_name} 已存在，跳过")
    
    # 删除旧字段（SQLite不支持直接删除列，需要重建表）
    old_fields = ['conditions', 'check_interval', 'last_check', 'last_trigger']
    has_old_fields = any(field in columns for field in old_fields)
    
    if has_old_fields:
        print("\n检测到旧字段，需要重建表...")
        print("⚠️  警告：此操作将删除旧的monitor_tasks数据")
        response = input("是否继续？(y/n): ")
        
        if response.lower() == 'y':
            # 备份数据
            cursor.execute("SELECT * FROM monitor_tasks")
            old_data = cursor.fetchall()
            print(f"备份了 {len(old_data)} 条记录")
            
            # 删除旧表
            cursor.execute("DROP TABLE monitor_tasks")
            
            # 创建新表
            cursor.execute("""
                CREATE TABLE monitor_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    update_schedule TEXT DEFAULT '09:30',
                    scan_schedule TEXT DEFAULT '15:30',
                    strategy TEXT DEFAULT 'default',
                    remark TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_update TEXT,
                    last_scan TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.commit()
            print("✅ 表重建成功")
            
            # 尝试迁移兼容的数据
            if old_data:
                print("尝试迁移数据...")
                for row in old_data:
                    try:
                        # 假设旧表结构：id, symbol, task_name, conditions, email, enabled, ...
                        cursor.execute("""
                            INSERT INTO monitor_tasks 
                            (symbol, task_name, email, enabled, created_at) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (row[1], row[2], row[4], row[5], row[-2] if len(row) > 10 else datetime.now()))
                    except Exception as e:
                        print(f"迁移记录失败: {e}")
                conn.commit()
                print(f"✅ 数据迁移完成")
        else:
            print("操作已取消")

print("\n当前表结构：")
cursor.execute("PRAGMA table_info(monitor_tasks)")
for row in cursor.fetchall():
    print(f"  {row[1]:20} {row[2]:10} {'NOT NULL' if row[3] else ''}")

print("\n✅ 数据库迁移完成")
conn.close()
