#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手后台服务测试脚本

测试所有 API 接口是否正常工作
"""

import requests
import json
import sys

# 后台服务地址
BASE_URL = "http://localhost:8100/api"

def test_health():
    """测试健康检查接口"""
    print("=" * 50)
    print("1. 测试健康检查接口 GET /api/health")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确认服务已启动")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_context():
    """测试获取上下文接口"""
    print("\n" + "=" * 50)
    print("2. 测试获取上下文接口 GET /api/context")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/context", timeout=5)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"system: {data.get('system', '')[:50]}...")
            print(f"context keys: {list(data.get('context', {}).keys())}")
            print(f"instructions: {data.get('instructions', '')[:50]}...")
            print("✅ 获取上下文成功")
            return True
        else:
            print(f"❌ 获取上下文失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_chat_sync():
    """测试同步聊天接口"""
    print("\n" + "=" * 50)
    print("3. 测试同步聊天接口 POST /api/chat/sync")
    print("=" * 50)

    try:
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好，请用一句话介绍自己"}
        ]

        response = requests.post(
            f"{BASE_URL}/chat/sync",
            json={"messages": messages},
            timeout=30
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"AI回复: {data.get('content', '')}")
            print("✅ 同步聊天测试成功")
            return True
        else:
            print(f"❌ 同步聊天失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_chat_stream():
    """测试流式聊天接口"""
    print("\n" + "=" * 50)
    print("4. 测试流式聊天接口 POST /api/chat")
    print("=" * 50)

    try:
        messages = [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好"}
        ]

        response = requests.post(
            f"{BASE_URL}/chat",
            json={"messages": messages, "stream": True},
            stream=True,
            timeout=30
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            print("流式响应内容:")
            full_content = ""
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        data_str = decoded[6:]
                        if data_str != '[DONE]':
                            try:
                                data = json.loads(data_str)
                                content = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    full_content += content
                                    print(content, end='', flush=True)
                            except:
                                pass
            print()
            print("✅ 流式聊天测试成功")
            return True
        else:
            print(f"❌ 流式聊天失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n🚀 AI助手后台服务测试")
    print(f"测试地址: {BASE_URL}\n")

    results = []

    # 测试健康检查
    results.append(("健康检查", test_health()))

    # 测试获取上下文
    results.append(("获取上下文", test_context()))

    # 测试同步聊天
    results.append(("同步聊天", test_chat_sync()))

    # 测试流式聊天
    results.append(("流式聊天", test_chat_stream()))

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查服务配置")
        return 1


if __name__ == '__main__':
    # 可以通过命令行参数指定服务地址
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]

    sys.exit(main())
