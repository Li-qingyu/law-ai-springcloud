package org.lawcommoncore.context;

public class BaseContext {

    public static ThreadLocal<Integer> threadLocal = new ThreadLocal<>();
    public static ThreadLocal<Integer> roleLocal = new ThreadLocal<>();
    public static ThreadLocal<Integer> guestIdLocal = new ThreadLocal<>();
    public static ThreadLocal<String> userTypeLocal = new ThreadLocal<>();
    /**
     * 内部调用标记：来自内部 Feign（X-Internal-Call）或 /internal/ 路径的请求为 true。
     * 授权切面（RequireRoleAspect）据此跳过角色校验，保证内部链路（如 dashboard 计数）不误拦。
     */
    public static ThreadLocal<Boolean> internalLocal = new ThreadLocal<>();

    public static void setCurrentId(Integer id) {
        threadLocal.set(id);
    }

    public static Integer getCurrentId() {
        return threadLocal.get();
    }

    public static void removeCurrentId() {
        threadLocal.remove();
    }

    public static void setCurrentRole(Integer role) {
        roleLocal.set(role);
    }

    public static Integer getCurrentRole() {
        return roleLocal.get();
    }

    public static void removeCurrentRole() {
        roleLocal.remove();
    }

    public static void setCurrentGuestId(Integer guestId) {
        guestIdLocal.set(guestId);
    }

    public static Integer getCurrentGuestId() {
        return guestIdLocal.get();
    }

    public static void removeCurrentGuestId() {
        guestIdLocal.remove();
    }

    public static void setUserType(String userType) {
        userTypeLocal.set(userType);
    }

    public static String getUserType() {
        return userTypeLocal.get();
    }

    public static void removeUserType() {
        userTypeLocal.remove();
    }

    public static void setInternal(boolean internal) {
        internalLocal.set(internal);
    }

    public static boolean isInternal() {
        return Boolean.TRUE.equals(internalLocal.get());
    }

    public static void removeInternal() {
        internalLocal.remove();
    }

    public static void clear() {
        threadLocal.remove();
        roleLocal.remove();
        guestIdLocal.remove();
        userTypeLocal.remove();
        internalLocal.remove();
    }

    /**
     * 将数据库角色转换为Agent需要的角色字符串
     * 0=普通用户, 1=超级管理员, 2=普通管理员
     */
    public static String getRoleString(Integer role) {
        if (role == null) return "user";
        switch (role) {
            case 1: return "super_admin";
            case 2: return "admin";
            default: return "user";
        }
    }

}
