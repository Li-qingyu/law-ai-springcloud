package org.lawaiservice.controller;

import com.alibaba.fastjson.JSONObject;
import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.utils.HttpClient;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.result.Result;
import org.lawcommonsecurity.annotation.RequireRole;
import org.lawcommonsecurity.constant.UserRole;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@RestController
@RequestMapping("/admin/ai")
@Slf4j
public class AdminAgentController {

    @Value("${python-ai-url:http://localhost:8000}")
    private String pythonAiUrl;
    private final ExecutorService executorService = Executors.newCachedThreadPool();

    /**
     * 流式管理接口 - SSE
     */
    @GetMapping("/manage/stream")
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public SseEmitter manageStream(@RequestParam String query, @RequestParam String sessionId) {
        log.info("流式管理请求: query={}, sessionId={}", query, sessionId);

        // 获取当前用户信息
        Integer currentUserId = BaseContext.getCurrentId();
        Integer currentRole = BaseContext.getCurrentRole();
        String userRole = BaseContext.getRoleString(currentRole);
        log.info("用户信息: userId={}, role={}, roleStr={}", currentUserId, currentRole, userRole);

        SseEmitter emitter = new SseEmitter(120000L);

        emitter.onTimeout(() -> {
            log.warn("SSE 连接超时: sessionId={}", sessionId);
            emitter.complete();
        });

        emitter.onError(e -> {
            log.error("SSE 连接错误: sessionId={}", sessionId, e);
        });

        executorService.execute(() -> {
            try {
                // 构建请求体
                JSONObject requestBody = new JSONObject();
                requestBody.put("query", query);
                requestBody.put("user_id", currentUserId);
                requestBody.put("user_role", userRole);
                requestBody.put("session_id", sessionId);

                // 流式调用 Python 服务
                HttpClient.doPostJsonStreaming(pythonAiUrl + "/admin/manage/stream", requestBody, eventData -> {
                    try {
                        JSONObject event = JSONObject.parseObject(eventData);
                        String type = event.getString("type");

                        if ("status".equals(type) || "progress".equals(type) || "token".equals(type)) {
                            // 转发状态、进度、token事件
                            emitter.send(eventData);
                        } else if ("confirm".equals(type)) {
                            // 确认事件 - 需要前端用户确认
                            emitter.send(eventData);
                        } else if ("complete".equals(type)) {
                            // 完成事件
                            emitter.send(eventData);
                        } else if ("error".equals(type)) {
                            // 错误事件
                            emitter.send(eventData);
                        }
                    } catch (Exception e) {
                        log.error("转发 SSE 事件失败", e);
                    }
                }, () -> {
                    // 流结束
                    emitter.complete();
                });

            } catch (Exception e) {
                log.error("流式管理请求失败", e);
                try {
                    JSONObject errorEvent = new JSONObject();
                    errorEvent.put("type", "error");
                    errorEvent.put("message", "服务调用失败: " + e.getMessage());
                    emitter.send(errorEvent.toJSONString());
                } catch (Exception ex) {
                    log.error("发送错误事件失败", ex);
                }
                emitter.complete();
            }
        });

        return emitter;
    }

    /**
     * 同步管理接口
     */
    @PostMapping("/manage")
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public Result<Object> manage(@RequestBody AdminManageRequest request) {
        log.info("同步管理请求: query={}", request.getQuery());

        try {
            Integer currentUserId = BaseContext.getCurrentId();
            Integer currentRole = BaseContext.getCurrentRole();
            String userRole = BaseContext.getRoleString(currentRole);

            JSONObject requestBody = new JSONObject();
            requestBody.put("query", request.getQuery());
            requestBody.put("user_id", currentUserId);
            requestBody.put("user_role", userRole);
            requestBody.put("session_id", request.getSessionId());

            String response = HttpClient.doPostJson(pythonAiUrl + "/admin/manage", requestBody);
            JSONObject result = JSONObject.parseObject(response);

            return Result.success(result);
        } catch (Exception e) {
            log.error("同步管理请求失败", e);
            return Result.error("服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 确认接口 - 恢复被interrupt暂停的子Agent
     */
    @PostMapping("/manage/confirm")
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public Result<Object> manageConfirm(@RequestBody AdminConfirmRequest request) {
        log.info("确认请求: threadId={}, agentType={}, answer={}", request.getThreadId(), request.getAgentType(), request.getAnswer());

        try {
            Integer currentUserId = BaseContext.getCurrentId();
            Integer currentRole = BaseContext.getCurrentRole();
            String userRole = BaseContext.getRoleString(currentRole);

            JSONObject requestBody = new JSONObject();
            requestBody.put("thread_id", request.getThreadId());
            requestBody.put("agent_type", request.getAgentType());
            requestBody.put("user_id", currentUserId);
            requestBody.put("user_role", userRole);
            requestBody.put("answer", request.getAnswer());

            String response = HttpClient.doPostJson(pythonAiUrl + "/admin/manage/confirm", requestBody);
            JSONObject result = JSONObject.parseObject(response);

            // Python 返回 {"code":200,"message":"success","data":{"result":"...","status":"..."}}
            // 提取内层 data 避免嵌套
            JSONObject innerData = result.getJSONObject("data");
            return Result.success(innerData != null ? innerData : result);
        } catch (Exception e) {
            log.error("确认请求失败", e);
            return Result.error("服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 请求体类
     */
    public static class AdminManageRequest {
        private String query;
        private String userRole;
        private String sessionId;

        public String getQuery() { return query; }
        public void setQuery(String query) { this.query = query; }
        public String getUserRole() { return userRole; }
        public void setUserRole(String userRole) { this.userRole = userRole; }
        public String getSessionId() { return sessionId; }
        public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    }

    /**
     * 确认请求体类
     */
    public static class AdminConfirmRequest {
        private String threadId;
        private String agentType;
        private String answer;

        public String getThreadId() { return threadId; }
        public void setThreadId(String threadId) { this.threadId = threadId; }
        public String getAgentType() { return agentType; }
        public void setAgentType(String agentType) { this.agentType = agentType; }
        public String getAnswer() { return answer; }
        public void setAnswer(String answer) { this.answer = answer; }
    }
}
