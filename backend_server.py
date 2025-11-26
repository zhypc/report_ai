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
    "instructions": "回答问题时要考虑报告内容，对于超出范围的问题要明确告知用户，回答问题不要使用Markdown格式。"
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

    # 如果指定了报告ID，可以从数据库或文件系统加载对应数据
    if report_id:
        # TODO: 根据 report_id 加载对应的上下文数据
        # context_data = load_context_by_report_id(report_id)
        pass

    context_data = load_context_data()
    return jsonify(context_data)


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
