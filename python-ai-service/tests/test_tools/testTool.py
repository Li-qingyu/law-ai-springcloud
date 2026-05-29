from app.repositories.milvus_client import init_milvus
from app.tools import LawArticleSearchTool, LawCaseSearchTool, ConsultHistorySearchTool,base_search_tool


if __name__ == '__main__':
    # 初始化 Milvus 连接
    print("正在初始化 Milvus 连接...")
    init_milvus()
    print("✓ Milvus 连接成功\n")


    # 法律条文搜索
    # 创建工具实例
    print("创建法律条文搜索工具...")
    tool1 = LawArticleSearchTool()
    print(f"✓ 工具创建成功")
    print(f"  - 名称: {tool1.name}")
    print(f"  - 描述: {tool1.description}")
    print(f"  - 集合: {tool1.collection_name}")
    print(f"  - Top-K: {tool1.top_k}\n")

    # 执行搜索
    query = "买卖不破租赁"
    print(f"执行搜索: '{query}'")
    print("=" * 60)
    result = tool1.invoke(query)
    print(result)
    print("=" * 60)

    # 案例搜索
    # 创建工具实例
    print("创建案例搜索工具...")
    tool = LawCaseSearchTool()
    print(f"✓ 工具创建成功")
    print(f"  - 名称: {tool.name}")
    print(f"  - 描述: {tool1.description}")
    print(f"  - 集合: {tool.collection_name}")
    print(f"  - Top-K: {tool.top_k}\n")

    # 执行搜索
    query = "买卖不破租赁"
    print(f"执行搜索: '{query}'")
    print("=" * 60)
    result = tool.invoke(query)
    print(result)
    print("=" * 60)

    # 咨询历史搜索
    # 创建工具实例
    print("创建咨询历史搜索工具...")
    tool = ConsultHistorySearchTool()
    print(f"✓ 工具创建成功")
    print(f"  - 名称: {tool.name}")
    print(f"  - 描述: {tool1.description}")
    print(f"  - 集合: {tool.collection_name}")
    print(f"  - Top-K: {tool.top_k}\n")

    # 执行搜索
    query = "买卖不破租赁"
    print(f"执行搜索: '{query}'")
    print("=" * 60)
    result = tool.invoke(query)
    print(result)
    print("=" * 60)
