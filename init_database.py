#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本

用于创建报告上下文数据表和插入示例数据
支持 MySQL 和 SQLite

使用方式：
    # MySQL
    export DB_TYPE=mysql
    export MYSQL_HOST=localhost
    export MYSQL_USER=root
    export MYSQL_PASSWORD=your_password
    export MYSQL_DATABASE=ai_assistant
    python init_database.py

    # SQLite
    export DB_TYPE=sqlite
    export SQLITE_PATH=report_context.db
    python init_database.py
"""

import os
import json
import sys

DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')

# MySQL 表创建语句
MYSQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS report_context (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(100) UNIQUE NOT NULL COMMENT '报告唯一标识',
    project_name VARCHAR(255) COMMENT '项目名称',
    system_prompt TEXT COMMENT '系统提示词',
    context_data JSON COMMENT '上下文JSON数据',
    instructions TEXT COMMENT '回答指令',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    INDEX idx_report_id (report_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# SQLite 表创建语句
SQLITE_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS report_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT UNIQUE NOT NULL,
    project_name TEXT,
    system_prompt TEXT,
    context_data TEXT,
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_report_id ON report_context(report_id);
CREATE INDEX IF NOT EXISTS idx_is_active ON report_context(is_active);
"""

# 示例数据
SAMPLE_DATA = {
    "report_id": "LUAD_2025_001",
    "project_name": "report中增加ai助手测试项目",
    "system_prompt": "你是一个专业的助手，下面是本次报告的内容，需要报告内容来回答问题。",
    "context_data": {
        "report_metadata": {
            "title": "空间转录组深度分析报告",
            "project_name": "report中增加ai助手测试项目",
            "sample_info": {
                "sample_id": "LUAD_S1, LUAD_S2",
                "slide_id": "LUAD_S1, LUAD_S2",
                "species": "hs",
                "tissue_type": "肺部"
            },
            "analysis_date": "2025-11-17",
            "pipeline_version": "深度分析"
        },
        "analysis_modules": {
            "1_0_loadData": {
                "module_name": "数据加载",
                "description": "原始数据加载和格式转换",
                "output_summary": "加载了278328个细胞，6738个基因",
                "key_metrics": {
                    "total_cells": 278328,
                    "total_genes": 6738
                }
            },
            "1_5_clusterReductionData": {
                "module_name": "聚类降维",
                "description": "降维聚类分析",
                "output_summary": "识别15个细胞群",
                "key_metrics": {
                    "n_clusters": 12,
                    "FindClusters_resolution": 0.2
                }
            },
            "2_1_labelTransfer": {
                "module_name": "细胞类型注释",
                "description": "基于参考数据集的细胞类型注释",
                "output_summary": "注释了40个细胞群的类型",
                "key_metrics": {
                    "reference_dataset": "GSE131907_Lung_Cancer_final_tLung"
                }
            },
            "3_2_CellChat2": {
                "module_name": "细胞通讯分析",
                "description": "分析细胞间的通讯网络",
                "output_summary": "识别了111个显著的细胞通讯对",
                "key_metrics": {
                    "signaling_pairs": 120
                }
            }
        }
    },
    "instructions": "回答问题时必须严格遵守以下规则：\n1. 必须基于上述报告内容回答问题，对于超出报告范围的问题要明确告知用户\n2. 【格式要求-必须遵守】回答必须使用纯文本格式，严禁使用任何Markdown语法，包括但不限于：**加粗**、*斜体*、# 标题、- 列表符号、1. 数字列表、``` 代码块、> 引用、[链接]() 等\n3. 使用普通的换行和空格来组织内容结构\n4. 回答要简洁准确，直接针对用户的问题"
}


def init_mysql():
    """初始化 MySQL 数据库"""
    import pymysql

    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', 3306))
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', '')
    database = os.environ.get('MYSQL_DATABASE', 'ai_assistant')

    print(f"Connecting to MySQL: {host}:{port}/{database}")

    try:
        # 先连接到MySQL服务器（不指定数据库）
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database '{database}' created or already exists")

        # 切换到数据库
        cursor.execute(f"USE {database}")

        # 创建表
        cursor.execute(MYSQL_CREATE_TABLE)
        conn.commit()
        print("Table 'report_context' created or already exists")

        # 插入示例数据
        insert_sql = """
            INSERT INTO report_context (report_id, project_name, system_prompt, context_data, instructions)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                project_name = VALUES(project_name),
                system_prompt = VALUES(system_prompt),
                context_data = VALUES(context_data),
                instructions = VALUES(instructions),
                updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(insert_sql, (
            SAMPLE_DATA["report_id"],
            SAMPLE_DATA["project_name"],
            SAMPLE_DATA["system_prompt"],
            json.dumps(SAMPLE_DATA["context_data"], ensure_ascii=False),
            SAMPLE_DATA["instructions"]
        ))
        conn.commit()
        print(f"Sample data inserted: report_id = {SAMPLE_DATA['report_id']}")

        cursor.close()
        conn.close()
        print("MySQL initialization completed!")
        return True

    except Exception as e:
        print(f"MySQL initialization failed: {e}")
        return False


def init_sqlite():
    """初始化 SQLite 数据库"""
    import sqlite3

    db_path = os.environ.get('SQLITE_PATH', 'report_context.db')
    print(f"Creating SQLite database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建表
        for statement in SQLITE_CREATE_TABLE.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        conn.commit()
        print("Table 'report_context' created or already exists")

        # 插入示例数据
        cursor.execute("""
            INSERT OR REPLACE INTO report_context
            (report_id, project_name, system_prompt, context_data, instructions)
            VALUES (?, ?, ?, ?, ?)
        """, (
            SAMPLE_DATA["report_id"],
            SAMPLE_DATA["project_name"],
            SAMPLE_DATA["system_prompt"],
            json.dumps(SAMPLE_DATA["context_data"], ensure_ascii=False),
            SAMPLE_DATA["instructions"]
        ))
        conn.commit()
        print(f"Sample data inserted: report_id = {SAMPLE_DATA['report_id']}")

        cursor.close()
        conn.close()
        print("SQLite initialization completed!")
        return True

    except Exception as e:
        print(f"SQLite initialization failed: {e}")
        return False


def main():
    print(f"\n{'='*50}")
    print("AI助手数据库初始化")
    print(f"{'='*50}\n")
    print(f"Database type: {DB_TYPE}")

    if DB_TYPE == 'mysql':
        success = init_mysql()
    elif DB_TYPE == 'sqlite':
        success = init_sqlite()
    else:
        print(f"Unsupported database type: {DB_TYPE}")
        print("Supported types: mysql, sqlite")
        success = False

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
