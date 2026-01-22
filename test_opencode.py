#!/usr/bin/env python3
"""OpenCode 连接测试脚本"""

import requests
import json
import sys

def test_opencode(port=4096):
    """测试 OpenCode API 连接"""
    base_url = f"http://127.0.0.1:{port}"

    print(f"测试 OpenCode 连接: {base_url}")
    print("=" * 50)

    # 测试 1: 健康检查
    print("\n[1] 测试健康检查...")
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        print(f"    状态码: {resp.status_code}")
        print(f"    响应: {resp.text[:200]}")
    except requests.exceptions.ConnectionError as e:
        print(f"    ❌ 连接失败: {e}")
        print(f"    提示: OpenCode 服务可能没有运行在端口 {port}")
        return False
    except Exception as e:
        print(f"    ❌ 错误: {e}")

    # 测试 2: 创建 session
    print("\n[2] 测试创建 Session...")
    try:
        resp = requests.post(f"{base_url}/session", json={}, timeout=10)
        print(f"    状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            session_id = data.get("id")
            print(f"    Session ID: {session_id}")
        else:
            print(f"    响应: {resp.text[:200]}")
    except Exception as e:
        print(f"    ❌ 错误: {e}")
        return False

    # 测试 3: 发送消息
    if 'session_id' in locals() and session_id:
        print(f"\n[3] 测试发送消息...")
        payload = {
            "agent": "general",
            "parts": [{"type": "text", "text": "你好"}]
        }
        try:
            resp = requests.post(
                f"{base_url}/session/{session_id}/message",
                json=payload,
                timeout=30
            )
            print(f"    状态码: {resp.status_code}")
            print(f"    响应长度: {len(resp.text)} 字符")
            print(f"    响应 (前300字符): {resp.text[:300]}...")
        except requests.exceptions.Timeout:
            print(f"    ❌ 请求超时 (30秒)")
            return False
        except Exception as e:
            print(f"    ❌ 错误: {e}")
            return False

    print("\n" + "=" * 50)
    print("测试完成!")
    return True


def scan_ports():
    """扫描可能的 OpenCode 端口"""
    ports = [4096, 3080, 5001, 5002, 8080, 3000]
    print("\n扫描可能的 OpenCode 端口...")
    for port in ports:
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
            print(f"  端口 {port}: ✓ 可连接")
            return port
        except:
            print(f"  端口 {port}: ✗ 不可连接")
    return None


if __name__ == "__main__":
    # 先扫描端口
    found_port = scan_ports()

    if found_port and found_port != 4096:
        print(f"\n发现 OpenCode 运行在端口 {found_port}!")
        print("是否使用此端口测试? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            test_opencode(found_port)
        else:
            test_opencode(4096)
    else:
        test_opencode(4096)
