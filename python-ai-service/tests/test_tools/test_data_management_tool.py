from app.tools.data_management_tool import DataManagementTool

def test_patent_data_management():
    """测试专利数据管理"""
    tool = DataManagementTool()
    result = tool._run("管理专利数据")
    assert "专利数据" in result

def test_company_data_management():
    """测试公司数据管理"""
    tool = DataManagementTool()
    result = tool._run("管理公司数据")
    assert "公司数据" in result

def test_lawsuit_data_management():
    """测试诉讼数据管理"""
    tool = DataManagementTool()
    result = tool._run("管理诉讼数据")
    assert "诉讼数据" in result

def test_law_data_management():
    """测试法律数据管理"""
    tool = DataManagementTool()
    result = tool._run("管理法律数据")
    assert "法律数据" in result

def test_unknown_operation():
    """测试未知操作"""
    tool = DataManagementTool()
    result = tool._run("未知操作")
    assert "请指定数据类型" in result
