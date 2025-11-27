#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手后台服务

提供以下接口：
- GET  /api/health   - 健康检查
- GET  /api/context  - 获取上下文数据
- POST /api/chat     - 聊天接口（流式响应）

启动方式：
    python backend_server.py

或使用 gunicorn（生产环境）：
    gunicorn -w 4 -b 0.0.0.0:8100 backend_server:app
"""

import os
import json
import base64
import requests
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

# 数据库支持（可选，根据需要启用）
DB_TYPE = os.environ.get('DB_TYPE', 'file')  # file, mysql, sqlite

if DB_TYPE == 'mysql':
    import pymysql
    pymysql.install_as_MySQLdb()
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import QueuePool
elif DB_TYPE == 'sqlite':
    import sqlite3

app = Flask(__name__)
# 启用跨域支持
CORS(app)

# ==================== 配置 ====================

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = 'deepseek-chat'

# 服务器配置
SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8100))
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'

# 上下文数据文件路径（可配置）
CONTEXT_FILE_PATH = os.environ.get('CONTEXT_FILE_PATH', 'context_data.json')

# 访问秘钥配置（可以设置多个秘钥，用逗号分隔）
VALID_ACCESS_KEYS = os.environ.get('VALID_ACCESS_KEYS', 'demo-key-123').split(',')

# ==================== 数据库配置 ====================

# MySQL 配置
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'ai_assistant')

# SQLite 配置
SQLITE_PATH = os.environ.get('SQLITE_PATH', 'report_context.db')

# 数据库连接池（MySQL）
db_engine = None
if DB_TYPE == 'mysql':
    try:
        db_url = f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
        db_engine = create_engine(db_url, poolclass=QueuePool, pool_size=5, max_overflow=10)
        print(f"MySQL connection pool created: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    except Exception as e:
        print(f"Failed to create MySQL connection: {e}")

# ==================== 上下文数据 ====================

# 默认上下文数据（如果没有配置文件，使用此默认数据）
DEFAULT_CONTEXT_DATA = {
    "system": "你是一个专业的助手，下面是本次报告的内容，需要报告内容来回答问题。",
    "context": {
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
            "1_1_qcData": {
                "module_name": "质量控制",
                "description": "数据质量评估和过滤",
                "output_summary": "过滤后剩余278328个细胞，6738个基因",
                "key_metrics": {
                    "filtered_cells": 0,
                    "filtered_genes": 0,
                    "mito_ratio_threshold": 0,
                    "doublet_score_threshold": 0
                }
            },
            "1_2_preprocessData": {
                "module_name": "数据预处理",
                "description": "标准化、归一化、批次校正",
                "output_summary": "完成标准化和批次校正",
                "key_metrics": {
                    "normalization_method": "LogNormalize",
                    "nFeatures": 3000
                }
            },
            "1_3_pcaData": {
                "module_name": "PCA分析",
                "description": "主成分分析",
                "output_summary": "完成了PCA主成分分析",
                "key_metrics": {
                    "n_pcs": 40
                }
            },
            "1_4_integrateData": {
                "module_name": "数据整合",
                "description": "多样本/多区域数据整合",
                "output_summary": "完成数据整合，识别批次效应",
                "key_metrics": {
                    "integration_method": "Harmony",
                    "dim_use": 30,
                    "k.weight": 50
                }
            },
            "1_5_clusterReductionData": {
                "module_name": "聚类降维",
                "description": "降维聚类分析",
                "output_summary": "识别15个细胞群",
                "key_metrics": {
                    "n_clusters": 12,
                    "FindClusters_resolution": 0.2,
                    "n.neighbors": 30
                }
            },
            "2_1_labelTransfer": {
                "module_name": "细胞类型注释",
                "description": "基于参考数据集的细胞类型注释",
                "output_summary": "注释了40个细胞群的类型",
                "key_metrics": {
                    "reference_dataset": "GSE131907_Lung_Cancer_final_tLung",
                    "sc_downSample_num": 100
                },
                "annotation_results": {
                    "cluster_0": {"type": "Fibroblasts", "confidence": 0.92},
                    "cluster_1": {"type": "Endothelial cells", "confidence": 0.88}
                }
            },
            "2_2_stRCTD": {
                "module_name": "空间解卷积",
                "description": "空间表达数据的细胞类型解卷积",
                "output_summary": "注释了36个细胞群的类型",
                "key_metrics": {
                    "doublet_mode": "doublet"
                }
            },
            "3_1_BuildNicheAssay": {
                "module_name": "生态位分析",
                "description": "构建生态位并分析细胞相互作用",
                "output_summary": "构建了4个生态位",
                "key_metrics": {
                    "neighbors.k": 20
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


def load_context_data():
    """
    加载上下文数据
    优先从配置文件加载，如果失败则使用默认数据
    """
    if os.path.exists(CONTEXT_FILE_PATH):
        try:
            with open(CONTEXT_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load context file: {e}")
    return DEFAULT_CONTEXT_DATA


def load_context_from_mysql(report_id):
    """
    从 MySQL 数据库加载上下文数据

    Args:
        report_id: 报告唯一标识

    Returns:
        dict: 上下文数据，如果未找到返回 None
    """
    if not db_engine:
        print("MySQL connection not available")
        return None

    try:
        with db_engine.connect() as conn:
            query = text("""
                SELECT system_prompt, context_data, instructions, project_name
                FROM report_context
                WHERE report_id = :report_id AND is_active = 1
                LIMIT 1
            """)
            result = conn.execute(query, {"report_id": report_id}).fetchone()

            if result:
                system_prompt, context_data, instructions, project_name = result

                # context_data 可能是 JSON 字符串或已解析的 dict
                if isinstance(context_data, str):
                    context_data = json.loads(context_data)

                return {
                    "system": system_prompt or DEFAULT_CONTEXT_DATA["system"],
                    "context": context_data or {},
                    "instructions": instructions or DEFAULT_CONTEXT_DATA["instructions"]
                }

            return None

    except Exception as e:
        print(f"MySQL query error: {e}")
        return None


def load_context_from_sqlite(report_id):
    """
    从 SQLite 数据库加载上下文数据

    Args:
        report_id: 报告唯一标识

    Returns:
        dict: 上下文数据，如果未找到返回 None
    """
    if not os.path.exists(SQLITE_PATH):
        print(f"SQLite database not found: {SQLITE_PATH}")
        return None

    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT system_prompt, context_data, instructions, project_name
            FROM report_context
            WHERE report_id = ? AND is_active = 1
            LIMIT 1
        """, (report_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            system_prompt, context_data, instructions, project_name = result

            # context_data 是 JSON 字符串
            if isinstance(context_data, str):
                context_data = json.loads(context_data)

            return {
                "system": system_prompt or DEFAULT_CONTEXT_DATA["system"],
                "context": context_data or {},
                "instructions": instructions or DEFAULT_CONTEXT_DATA["instructions"]
            }

        return None

    except Exception as e:
        print(f"SQLite query error: {e}")
        return None


def load_context_by_report_id(report_id):
    """
    根据报告ID加载上下文数据（统一入口）

    Args:
        report_id: 报告唯一标识

    Returns:
        dict: 上下文数据
    """
    context_data = None

    if DB_TYPE == 'mysql':
        context_data = load_context_from_mysql(report_id)
    elif DB_TYPE == 'sqlite':
        context_data = load_context_from_sqlite(report_id)

    # 如果数据库中未找到，尝试从文件加载
    if context_data is None:
        context_data = load_context_data()

    return context_data


# ==================== 工具提示词数据 ====================

# 默认工具提示词数据
DEFAULT_TOOLS_PROMPT = {
    "tools_system_prompt": "你是一个专业的生物信息学分析助手。以下是平台支持的所有分析模块，当用户的报告中缺少某些分析，或用户提出的问题涉及未进行的分析时，你可以根据用户需求推荐合适的分析模块。",
    "recommendation_instructions": "推荐分析时请遵循以下原则：\n1. 根据用户的研究目的和数据类型推荐最相关的分析\n2. 简要说明推荐该分析的理由和预期收获\n3. 如果多个分析模块相关，按优先级排序推荐\n4. 对于已完成的分析，不要重复推荐",
    "tools_data": {}
}

# 工具提示词文件路径
TOOLS_PROMPT_FILE_PATH = os.environ.get('TOOLS_PROMPT_FILE_PATH', 'tools_prompt.json')


def load_tools_prompt_from_file():
    """从文件加载工具提示词数据"""
    if os.path.exists(TOOLS_PROMPT_FILE_PATH):
        try:
            with open(TOOLS_PROMPT_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load tools prompt file: {e}")
    return DEFAULT_TOOLS_PROMPT


def load_tools_prompt_from_mysql(prompt_id='default_tools_prompt'):
    """从 MySQL 数据库加载工具提示词数据"""
    if not db_engine:
        print("MySQL connection not available")
        return None

    try:
        with db_engine.connect() as conn:
            query = text("""
                SELECT tools_system_prompt, recommendation_instructions, tools_data
                FROM tools_prompt
                WHERE prompt_id = :prompt_id AND is_active = 1
                LIMIT 1
            """)
            result = conn.execute(query, {"prompt_id": prompt_id}).fetchone()

            if result:
                tools_system_prompt, recommendation_instructions, tools_data = result

                if isinstance(tools_data, str):
                    tools_data = json.loads(tools_data)

                return {
                    "tools_system_prompt": tools_system_prompt or DEFAULT_TOOLS_PROMPT["tools_system_prompt"],
                    "recommendation_instructions": recommendation_instructions or DEFAULT_TOOLS_PROMPT["recommendation_instructions"],
                    "tools_data": tools_data or {}
                }

            return None

    except Exception as e:
        print(f"MySQL query error for tools_prompt: {e}")
        return None


def load_tools_prompt_from_sqlite(prompt_id='default_tools_prompt'):
    """从 SQLite 数据库加载工具提示词数据"""
    if not os.path.exists(SQLITE_PATH):
        print(f"SQLite database not found: {SQLITE_PATH}")
        return None

    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tools_system_prompt, recommendation_instructions, tools_data
            FROM tools_prompt
            WHERE prompt_id = ? AND is_active = 1
            LIMIT 1
        """, (prompt_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            tools_system_prompt, recommendation_instructions, tools_data = result

            if isinstance(tools_data, str):
                tools_data = json.loads(tools_data)

            return {
                "tools_system_prompt": tools_system_prompt or DEFAULT_TOOLS_PROMPT["tools_system_prompt"],
                "recommendation_instructions": recommendation_instructions or DEFAULT_TOOLS_PROMPT["recommendation_instructions"],
                "tools_data": tools_data or {}
            }

        return None

    except Exception as e:
        print(f"SQLite query error for tools_prompt: {e}")
        return None


def load_tools_prompt(prompt_id='default_tools_prompt'):
    """
    加载工具提示词数据（统一入口）

    Args:
        prompt_id: 提示词ID，默认为 'default_tools_prompt'

    Returns:
        dict: 工具提示词数据
    """
    tools_prompt = None

    if DB_TYPE == 'mysql':
        tools_prompt = load_tools_prompt_from_mysql(prompt_id)
    elif DB_TYPE == 'sqlite':
        tools_prompt = load_tools_prompt_from_sqlite(prompt_id)

    # 如果数据库中未找到，尝试从文件加载
    if tools_prompt is None:
        tools_prompt = load_tools_prompt_from_file()

    return tools_prompt


def decode_base64_context(base64_str):
    """
    解码 Base64 编码的上下文数据
    """
    try:
        decoded = base64.b64decode(base64_str)
        return json.loads(decoded.decode('utf-8'))
    except Exception as e:
        print(f"Error decoding base64 context: {e}")
        return None


# ==================== 秘钥验证 ====================

def verify_access_key(key):
    """
    验证访问秘钥是否有效
    """
    if not key:
        return False
    return key.strip() in [k.strip() for k in VALID_ACCESS_KEYS]


def get_access_key_from_request():
    """
    从请求中获取访问秘钥
    支持从 X-Access-Key 头部或 Authorization Bearer 头部获取
    """
    # 优先从 X-Access-Key 头部获取
    key = request.headers.get('X-Access-Key')
    if key:
        return key.strip()

    # 从 Authorization Bearer 头部获取
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:].strip()

    return None


def require_auth(f):
    """
    装饰器：要求访问秘钥验证
    """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = get_access_key_from_request()
        if not verify_access_key(key):
            return jsonify({"error": "访问秘钥无效或未提供"}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== API 接口 ====================

@app.route('/api/verify', methods=['POST'])
def verify_key():
    """
    验证访问秘钥接口
    用于前端验证用户输入的秘钥是否有效
    """
    key = get_access_key_from_request()

    # 也可以从请求体获取
    if not key and request.json:
        key = request.json.get('key', '')

    if verify_access_key(key):
        return jsonify({
            "valid": True,
            "message": "验证成功"
        }), 200
    else:
        return jsonify({
            "valid": False,
            "message": "秘钥无效或已过期"
        }), 401


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    用于检测服务是否正常运行
    """
    # 检查 API Key 是否配置
    api_key_configured = bool(DEEPSEEK_API_KEY)

    return jsonify({
        "status": "ok",
        "api_key_configured": api_key_configured,
        "version": "1.0.0"
    }), 200


@app.route('/api/context', methods=['GET'])
@require_auth
def get_context():
    """
    获取上下文数据接口
    返回报告的元数据和分析结果，供 AI 作为背景知识

    可选参数：
    - report_id: 报告ID，用于获取特定报告的上下文
    """
    report_id = request.args.get('report_id')

    # 根据数据源类型加载上下文
    if report_id and DB_TYPE in ('mysql', 'sqlite'):
        context_data = load_context_by_report_id(report_id)
    else:
        context_data = load_context_data()

    return jsonify(context_data)


@app.route('/api/tools_prompt', methods=['GET'])
@require_auth
def get_tools_prompt():
    """
    获取工具提示词数据接口
    返回平台支持的分析模块信息，用于向用户推荐分析

    可选参数：
    - prompt_id: 提示词ID，默认为 'default_tools_prompt'
    """
    prompt_id = request.args.get('prompt_id', 'default_tools_prompt')
    tools_prompt = load_tools_prompt(prompt_id)
    return jsonify(tools_prompt)


@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    """
    聊天接口（流式响应）

    请求体：
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."}
        ],
        "stream": true
    }

    响应：SSE 流式数据
    """
    # 检查 API Key
    if not DEEPSEEK_API_KEY:
        return jsonify({"error": "API Key 未配置，请联系管理员"}), 500

    # 解析请求
    try:
        data = request.json
        messages = data.get('messages', [])
        stream = data.get('stream', True)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)
    except Exception as e:
        return jsonify({"error": f"请求格式错误: {str(e)}"}), 400

    if not messages:
        return jsonify({"error": "messages 不能为空"}), 400

    def generate_stream():
        """
        生成流式响应
        """
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': DEEPSEEK_MODEL,
                    'messages': messages,
                    'stream': stream,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                },
                stream=True,
                timeout=60
            )

            if response.status_code != 200:
                error_msg = response.text
                yield f'data: {{"error": "API请求失败: {error_msg}"}}\n\n'
                return

            # 转发流式响应
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    yield decoded_line + '\n'

        except requests.exceptions.Timeout:
            yield 'data: {"error": "请求超时，请稍后重试"}\n\n'
        except requests.exceptions.ConnectionError:
            yield 'data: {"error": "网络连接失败，请检查网络"}\n\n'
        except Exception as e:
            yield f'data: {{"error": "服务器错误: {str(e)}"}}\n\n'

    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # 禁用 nginx 缓冲
        }
    )


@app.route('/api/chat/sync', methods=['POST'])
@require_auth
def chat_sync():
    """
    同步聊天接口（非流式）
    用于不支持流式响应的场景
    """
    if not DEEPSEEK_API_KEY:
        return jsonify({"error": "API Key 未配置，请联系管理员"}), 500

    try:
        data = request.json
        messages = data.get('messages', [])
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)
    except Exception as e:
        return jsonify({"error": f"请求格式错误: {str(e)}"}), 400

    if not messages:
        return jsonify({"error": "messages 不能为空"}), 400

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': DEEPSEEK_MODEL,
                'messages': messages,
                'stream': False,
                'temperature': temperature,
                'max_tokens': max_tokens
            },
            timeout=60
        )

        if response.status_code != 200:
            return jsonify({"error": f"API请求失败: {response.text}"}), response.status_code

        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')

        return jsonify({
            "content": content,
            "usage": result.get('usage', {})
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "请求超时，请稍后重试"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "网络连接失败"}), 502
    except Exception as e:
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "接口不存在"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "服务器内部错误"}), 500


# ==================== 启动服务 ====================

if __name__ == '__main__':
    # 检查 API Key 配置
    if not DEEPSEEK_API_KEY:
        print("Warning: DEEPSEEK_API_KEY 未配置!")
        print("请设置环境变量: export DEEPSEEK_API_KEY='your-api-key'")
        print("")

    print(f"Starting AI Assistant Backend Server...")
    print(f"Server: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"Health Check: http://{SERVER_HOST}:{SERVER_PORT}/api/health")
    print(f"Debug Mode: {DEBUG_MODE}")
    print("")

    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=DEBUG_MODE
    )
