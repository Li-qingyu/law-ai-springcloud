from app.tools.adminTool.file_management_tool import FileManagementTool

def test_file_upload():
    """测试文件上传"""
    tool = FileManagementTool()
    result = tool._run("上传文件 patent_data.xlsx")
    assert "上传成功" in result

def test_file_parse():
    """测试文件解析"""
    tool = FileManagementTool()
    result = tool._run("解析文件 patent_data.pdf")
    assert "解析完成" in result

def test_file_import():
    """测试批量导入"""
    tool = FileManagementTool()
    result = tool._run("导入数据 patent_data.csv")
    assert "导入完成" in result

def test_unknown_operation():
    """测试未知操作"""
    tool = FileManagementTool()
    result = tool._run("未知操作")
    assert "请指定操作类型" in result
