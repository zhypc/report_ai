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

# MySQL 表创建语句 - 报告上下文表
MYSQL_CREATE_REPORT_TABLE = """
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

# MySQL 表创建语句 - 工具提示词表
MYSQL_CREATE_TOOLS_TABLE = """
CREATE TABLE IF NOT EXISTS tools_prompt (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prompt_id VARCHAR(100) UNIQUE NOT NULL COMMENT '提示词唯一标识',
    tools_system_prompt TEXT COMMENT '工具系统提示词',
    recommendation_instructions TEXT COMMENT '推荐指令',
    tools_data JSON COMMENT '工具JSON数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    INDEX idx_prompt_id (prompt_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# SQLite 表创建语句 - 报告上下文表
SQLITE_CREATE_REPORT_TABLE = """
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

# SQLite 表创建语句 - 工具提示词表
SQLITE_CREATE_TOOLS_TABLE = """
CREATE TABLE IF NOT EXISTS tools_prompt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id TEXT UNIQUE NOT NULL,
    tools_system_prompt TEXT,
    recommendation_instructions TEXT,
    tools_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_tools_prompt_id ON tools_prompt(prompt_id);
CREATE INDEX IF NOT EXISTS idx_tools_is_active ON tools_prompt(is_active);
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

# 工具提示词示例数据
TOOLS_PROMPT_DATA = {
    "prompt_id": "default_tools_prompt",
    "tools_system_prompt": "你是一个专业的生物信息学分析助手。以下是平台支持的所有分析模块，当用户的报告中缺少某些分析，或用户提出的问题涉及未进行的分析时，你可以根据用户需求推荐合适的分析模块。",
    "recommendation_instructions": "推荐分析时请遵循以下原则：\n1. 根据用户的研究目的和数据类型推荐最相关的分析\n2. 简要说明推荐该分析的理由和预期收获\n3. 如果多个分析模块相关，按优先级排序推荐\n4. 对于已完成的分析，不要重复推荐",
    "tools_data": {
        "单细胞RNA分析工具": {
            "基础处理模块": {
                "loadData": {"description": "数据加载模块", "recommendation": "如果您有新的单细胞数据需要分析，可以通过此模块导入数据"},
                "qcData": {"description": "质量控制模块", "recommendation": "建议在正式分析前进行质控"},
                "preprocessData": {"description": "数据预处理模块", "recommendation": "数据预处理是下游分析的基础"},
                "pcaData": {"description": "PCA降维模块", "recommendation": "PCA分析有助于理解数据的整体结构"},
                "integrateData": {"description": "批次整合模块", "recommendation": "如果您的数据包含多个样本或批次，建议进行批次整合"},
                "clusterReductionData": {"description": "聚类降维模块", "recommendation": "聚类分析可以识别不同的细胞群体"}
            },
            "细胞注释模块": {
                "autoAnnotationData": {"description": "自动注释模块", "recommendation": "如果您需要快速了解数据中的细胞类型组成，建议使用自动注释"},
                "celltypist": {"description": "CellTypist注释模块", "recommendation": "如果需要更精细的免疫细胞分型，建议使用 CellTypist"},
                "subclusterAnno": {"description": "亚群分析模块", "recommendation": "如果您对某类细胞感兴趣，建议进行亚群细分分析"}
            },
            "轨迹分析模块": {
                "Cytotrace": {"description": "发育潜能分析模块", "recommendation": "如果您想了解细胞的发育状态，建议进行 CytoTRACE 分析"},
                "monocle2": {"description": "拟时序分析模块", "recommendation": "如果您想研究细胞的分化过程，建议使用 Monocle2"},
                "velocity": {"description": "RNA速率分析模块", "recommendation": "如果您想了解细胞的瞬时转录动态，建议进行 RNA velocity 分析"}
            },
            "细胞通讯模块": {
                "CellChat": {"description": "CellChat通讯分析模块", "recommendation": "如果您想了解不同细胞类型之间的相互作用，建议进行 CellChat 分析"},
                "CellphoneDB": {"description": "CellphoneDB通讯分析模块", "recommendation": "CellphoneDB 可以提供详细的配体-受体相互作用信息"},
                "NicheNet": {"description": "NicheNet信号分析模块", "recommendation": "如果您想了解上游信号如何影响下游基因表达，建议使用 NicheNet"}
            },
            "调控网络模块": {
                "SCENIC": {"description": "转录调控网络模块", "recommendation": "如果您想了解关键转录因子及其调控网络，建议进行 SCENIC 分析"},
                "hdWGCNA": {"description": "共表达网络模块", "recommendation": "如果您想识别共表达基因模块，建议进行 hdWGCNA 分析"}
            },
            "临床分析模块": {
                "inferCNV": {"description": "拷贝数变异分析模块", "recommendation": "如果您想识别肿瘤细胞，建议进行 inferCNV 分析"},
                "ScPharm": {"description": "药物反应分析模块", "recommendation": "如果您想预测药物敏感性，建议进行 ScPharm 分析"}
            }
        },
        "单细胞空间转录组分析工具": {
            "基础处理模块": {
                "loadData": {"description": "空间数据加载模块", "recommendation": "如果您有新的空间转录组数据，可以通过此模块导入"},
                "qcData": {"description": "空间数据质控模块", "recommendation": "建议对空间数据进行质控"},
                "clusterReductionData": {"description": "空间聚类模块", "recommendation": "聚类分析可以识别空间上不同的区域"}
            },
            "空间聚类模块": {
                "BANKSY": {"description": "BANKSY空间聚类模块", "recommendation": "如果您想利用空间邻域信息进行聚类，建议使用 BANKSY"},
                "cellcharter": {"description": "空间社区识别模块", "recommendation": "如果您想识别空间社区，建议使用 cellcharter"}
            },
            "细胞注释与去卷积模块": {
                "labelTransfer": {"description": "标签迁移模块", "recommendation": "如果您有配套的单细胞数据，建议使用标签迁移"},
                "stRCTD": {"description": "RCTD去卷积模块", "recommendation": "RCTD 是可靠的空间去卷积方法"},
                "SPOTlight": {"description": "SPOTlight去卷积模块", "recommendation": "如果您想了解每个 spot 的细胞类型组成，建议进行去卷积分析"}
            },
            "空间微环境模块": {
                "BuildNicheAssay": {"description": "Niche构建模块", "recommendation": "如果您想研究空间微环境，建议先构建 Niche assay"}
            },
            "空间通讯模块": {
                "CellChat2": {"description": "空间CellChat模块", "recommendation": "如果您想了解空间上的细胞通讯，建议进行空间 CellChat 分析"}
            },
            "空间轨迹与调控模块": {
                "SpaTrack": {"description": "空间轨迹追踪模块", "recommendation": "如果您想了解细胞在组织中的迁移路径，建议进行 SpaTrack 分析"},
                "SpaGRN": {"description": "空间调控网络模块", "recommendation": "如果您想了解空间上的基因调控关系，建议进行 SpaGRN 分析"}
            }
        }
    }
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

        # 创建报告上下文表
        cursor.execute(MYSQL_CREATE_REPORT_TABLE)
        conn.commit()
        print("Table 'report_context' created or already exists")

        # 创建工具提示词表
        cursor.execute(MYSQL_CREATE_TOOLS_TABLE)
        conn.commit()
        print("Table 'tools_prompt' created or already exists")

        # 插入报告上下文示例数据
        insert_report_sql = """
            INSERT INTO report_context (report_id, project_name, system_prompt, context_data, instructions)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                project_name = VALUES(project_name),
                system_prompt = VALUES(system_prompt),
                context_data = VALUES(context_data),
                instructions = VALUES(instructions),
                updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(insert_report_sql, (
            SAMPLE_DATA["report_id"],
            SAMPLE_DATA["project_name"],
            SAMPLE_DATA["system_prompt"],
            json.dumps(SAMPLE_DATA["context_data"], ensure_ascii=False),
            SAMPLE_DATA["instructions"]
        ))
        conn.commit()
        print(f"Report context inserted: report_id = {SAMPLE_DATA['report_id']}")

        # 插入工具提示词数据
        insert_tools_sql = """
            INSERT INTO tools_prompt (prompt_id, tools_system_prompt, recommendation_instructions, tools_data)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                tools_system_prompt = VALUES(tools_system_prompt),
                recommendation_instructions = VALUES(recommendation_instructions),
                tools_data = VALUES(tools_data),
                updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(insert_tools_sql, (
            TOOLS_PROMPT_DATA["prompt_id"],
            TOOLS_PROMPT_DATA["tools_system_prompt"],
            TOOLS_PROMPT_DATA["recommendation_instructions"],
            json.dumps(TOOLS_PROMPT_DATA["tools_data"], ensure_ascii=False)
        ))
        conn.commit()
        print(f"Tools prompt inserted: prompt_id = {TOOLS_PROMPT_DATA['prompt_id']}")

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

        # 创建报告上下文表
        for statement in SQLITE_CREATE_REPORT_TABLE.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        conn.commit()
        print("Table 'report_context' created or already exists")

        # 创建工具提示词表
        for statement in SQLITE_CREATE_TOOLS_TABLE.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        conn.commit()
        print("Table 'tools_prompt' created or already exists")

        # 插入报告上下文示例数据
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
        print(f"Report context inserted: report_id = {SAMPLE_DATA['report_id']}")

        # 插入工具提示词数据
        cursor.execute("""
            INSERT OR REPLACE INTO tools_prompt
            (prompt_id, tools_system_prompt, recommendation_instructions, tools_data)
            VALUES (?, ?, ?, ?)
        """, (
            TOOLS_PROMPT_DATA["prompt_id"],
            TOOLS_PROMPT_DATA["tools_system_prompt"],
            TOOLS_PROMPT_DATA["recommendation_instructions"],
            json.dumps(TOOLS_PROMPT_DATA["tools_data"], ensure_ascii=False)
        ))
        conn.commit()
        print(f"Tools prompt inserted: prompt_id = {TOOLS_PROMPT_DATA['prompt_id']}")

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
