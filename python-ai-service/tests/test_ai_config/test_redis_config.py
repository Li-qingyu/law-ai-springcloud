"""
AI 配置 Redis 读取测试

验证 Java 端是否已将 AI 配置正确写入 Redis，以及 Python 端能否正常读取。

注意：Java 端 Jackson 序列化使用驼峰命名，Redis 中的 JSON 字段为：
    provider / modelName / apiKey / apiBaseUrl / isDefault / status / maxTokens / temperature
后续 Python ConfigManager 的 AiConfig dataclass 需与此对齐。

运行方式:
    cd python-ai-service
    python -m pytest tests/test_ai_config/test_redis_config.py -v -s

    # 或直接运行（不依赖 pytest）
    python tests/test_ai_config/test_redis_config.py
"""
import json
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.repositories.redis_client import get_redis


# Redis Key 常量（与 Java 端 AiConfigServiceImpl 保持一致）
KEY_DEFAULT = "ai:config:default"
KEY_PROVIDERS = "ai:config:providers"
KEY_ALL_KEYS = "ai:config:all_keys"


def test_redis_connection():
    """测试 Redis 连接是否正常"""
    r = get_redis()
    assert r.ping(), "Redis 连接失败"
    print("\n✅ Redis 连接成功")


def test_java_config_exists():
    """测试 Java 端是否已写入配置（检查 default key）"""
    r = get_redis()
    data = r.get(KEY_DEFAULT)

    if data is None:
        print(f"\n⚠️  Redis 中不存在 {KEY_DEFAULT}，Java 端可能尚未同步配置")
        print("   请先在管理端添加一条 AI 配置并设为默认，或触发 setDefault 操作")
        return None

    config = json.loads(data)
    print(f"\n✅ 读取到默认配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
    return config


def test_default_config_structure():
    """测试默认配置的 JSON 结构是否完整"""
    r = get_redis()
    data = r.get(KEY_DEFAULT)
    if data is None:
        print(f"\n⚠️  跳过：{KEY_DEFAULT} 不存在")
        return

    config = json.loads(data)

    # Java Jackson 序列化使用驼峰命名
    required_fields = ["provider", "modelName", "apiKey"]
    for field in required_fields:
        assert field in config, f"缺少必要字段: {field}"
        assert config[field], f"字段 {field} 为空"

    # 可选但期望存在的字段
    optional_fields = ["apiBaseUrl", "maxTokens", "temperature", "status"]
    for field in optional_fields:
        if field in config:
            print(f"   {field}: {config[field]}")

    print(f"\n✅ 默认配置结构完整")
    print(f"   provider: {config['provider']}")
    print(f"   modelName: {config['modelName']}")
    print(f"   apiKey: {config['apiKey'][:10]}...（已脱敏）")
    print(f"   apiBaseUrl: {config.get('apiBaseUrl', 'N/A')}")


def test_provider_configs():
    """测试按 provider 维度的配置是否存在"""
    r = get_redis()

    # 检查 providers 集合
    providers = r.smembers(KEY_PROVIDERS)
    if not providers:
        print(f"\n⚠️  Redis 中不存在 {KEY_PROVIDERS}，无 provider 信息")
        return

    print(f"\n✅ 已注册的 provider: {providers}")

    # 检查每个 provider 的配置 key
    all_keys = r.smembers(KEY_ALL_KEYS)
    if all_keys:
        print(f"   活跃配置 key: {all_keys}")

    for key in (all_keys or []):
        data = r.get(key)
        if data:
            config = json.loads(data)
            print(f"   ✓ {key} → provider={config.get('provider')}, model={config.get('modelName')}")
        else:
            print(f"   ✗ {key} → 数据不存在（key 已跟踪但 Redis 中缺失）")


def test_all_config_keys():
    """测试 ai:config:all_keys 跟踪集合是否正常"""
    r = get_redis()
    keys = r.smembers(KEY_ALL_KEYS)

    if not keys:
        print(f"\n⚠️  {KEY_ALL_KEYS} 为空或不存在，可能 Java 端尚未同步")
        return

    print(f"\n✅ 跟踪集合中有 {len(keys)} 个配置 key:")
    for key in sorted(keys):
        exists = r.exists(key)
        status = "✓ 存在" if exists else "✗ 缺失"
        print(f"   {key} → {status}")


def test_read_specific_provider():
    """测试读取指定 provider 的配置"""
    r = get_redis()

    # 先获取 providers 列表
    providers = r.smembers(KEY_PROVIDERS)
    if not providers:
        print(f"\n⚠️  无 provider 信息，跳过")
        return

    # 取第一个 provider 测试
    provider = sorted(providers)[0]
    default_key = f"ai:config:{provider}"

    # 尝试直接读 provider key（旧格式，可能不存在）
    data = r.get(default_key)
    if data:
        print(f"\n✅ 读取到 {default_key}:")
        config = json.loads(data)
        print(f"   modelName: {config.get('modelName')}")
    else:
        print(f"\n⚠️  {default_key} 不存在（正常，新格式为 ai:config:{{provider}}:{{model_name}}）")

    # 遍历 all_keys 找该 provider 的配置
    all_keys = r.smembers(KEY_ALL_KEYS)
    found = False
    for key in (all_keys or []):
        if key.startswith(f"ai:config:{provider}:"):
            data = r.get(key)
            if data:
                config = json.loads(data)
                print(f"   ✓ {key} → model={config.get('modelName')}, apiKey={config.get('apiKey', '')[:10]}...")
                found = True

    if not found:
        print(f"   未找到 provider={provider} 的配置")


def test_all_configs_readable():
    """测试所有配置均可正常读取并包含关键字段"""
    r = get_redis()
    all_keys = r.smembers(KEY_ALL_KEYS)
    if not all_keys:
        print(f"\n⚠️  无配置 key，跳过")
        return

    errors = []
    for key in sorted(all_keys):
        data = r.get(key)
        if not data:
            errors.append(f"{key}: 数据为空")
            continue
        config = json.loads(data)
        # 校验关键字段
        for field in ["provider", "modelName", "apiKey"]:
            if not config.get(field):
                errors.append(f"{key}: 缺少字段 {field}")

    if errors:
        for e in errors:
            print(f"   ✗ {e}")
        raise AssertionError(f"共 {len(errors)} 个配置校验失败")
    else:
        print(f"\n✅ 全部 {len(all_keys)} 个配置校验通过")
        for key in sorted(all_keys):
            config = json.loads(r.get(key))
            print(f"   {config['provider']}/{config['modelName']} → apiKey={config['apiKey'][:10]}...")


# ==================== 独立运行入口 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("AI 配置 Redis 读取测试")
    print("=" * 60)

    tests = [
        ("Redis 连接", test_redis_connection),
        ("默认配置存在性", test_java_config_exists),
        ("默认配置结构", test_default_config_structure),
        ("Provider 配置", test_provider_configs),
        ("跟踪集合", test_all_config_keys),
        ("指定 Provider 读取", test_read_specific_provider),
        ("全部配置校验", test_all_configs_readable),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for name, test_fn in tests:
        try:
            print(f"\n{'─' * 40}")
            print(f"测试: {name}")
            print(f"{'─' * 40}")
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ 失败: {e}")
            failed += 1
        except Exception as e:
            if "连接" in str(e) or "Connection" in str(e):
                print(f"\n⏭️  跳过: Redis 连接失败 - {e}")
                skipped += 1
            else:
                print(f"\n❌ 异常: {e}")
                failed += 1

    print(f"\n{'=' * 60}")
    print(f"结果: 通过={passed}, 失败={failed}, 跳过={skipped}")
    print(f"{'=' * 60}")
