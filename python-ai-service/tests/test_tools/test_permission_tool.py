from app.tools.adminTool.permission_tool import PermissionTool

def test_user_management():
    """测试用户管理"""
    tool = PermissionTool()
    result = tool._run("管理用户")
    assert "用户管理" in result

def test_role_management():
    """测试角色管理"""
    tool = PermissionTool()
    result = tool._run("管理角色")
    assert "角色管理" in result

def test_permission_management():
    """测试权限管理"""
    tool = PermissionTool()
    result = tool._run("管理权限")
    assert "权限管理" in result

def test_unknown_operation():
    """测试未知操作"""
    tool = PermissionTool()
    result = tool._run("未知操作")
    assert "请指定操作类型" in result
