package org.lawaiservice.controller;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.client.AiConsultResponse;
import org.lawaiservice.client.PythonRequest;
import org.lawaiservice.feign.GuestFeignClient;
import org.lawaiservice.feign.LawServiceFeignClient;
import org.lawaiservice.mapper.AiConsultationMapper;
import org.lawaiservice.mapper.GuestConsultationMapper;
import org.lawaiservice.service.AIConsultService;
import org.lawaiservice.utils.HttpClient;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.dto.AiConsultDTO;
import org.lawcommoncore.entity.AiConsultation;
import org.lawcommoncore.entity.ConversationHistory;
import org.lawcommoncore.entity.GuestConsultation;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.AiConsultationDetailVO;
import org.lawcommoncore.vo.AiSessionHistoryVO;
import org.lawcommoncore.vo.GuestInfoVO;
import org.lawcommoncore.vo.LawCaseVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@RestController
@RequestMapping("/user/ai")
@Slf4j
public class AIConsultController {
    @Autowired
    private AIConsultService aiConsultService;
    @Autowired
    private LawServiceFeignClient lawServiceFeignClient;
    @Autowired
    private GuestFeignClient guestFeignClient;
    @Autowired
    private AiConsultationMapper aiConsultationMapper;
    @Autowired
    private GuestConsultationMapper guestConsultationMapper;

    private static final String STREAM_URL = "http://localhost:8000/v1/ai/consult/stream";
    private final ExecutorService executorService = Executors.newCachedThreadPool();

    @PostMapping("/consult")
    public Result<AiConsultResponse> consult(@RequestBody AiConsultDTO aiConsultDTO){
        log.info("ai咨询：{}" , aiConsultDTO);
         return Result.success(aiConsultService.consult(aiConsultDTO.getQuestion(), aiConsultDTO.getSessionId() ));
    }

    @GetMapping("/consult/stream")
    public SseEmitter consultStream(@RequestParam String question, @RequestParam String sessionId) {
        log.info("流式ai咨询：question={}, sessionId={}", question, sessionId);

        // 在主线程中捕获用户/游客信息（ThreadLocal 在异步线程中不可用）
        String userType = BaseContext.getUserType();
        Integer currentUserId = null;
        Integer currentGuestId = null;

        if ("guest".equals(userType)) {
            currentGuestId = BaseContext.getCurrentGuestId();
            Result<Boolean> canAsk = guestFeignClient.canAsk(currentGuestId);
            if (!Boolean.TRUE.equals(canAsk.getData())) {
                SseEmitter errorEmitter = new SseEmitter();
                try {
                    JSONObject errorEvent = new JSONObject();
                    errorEvent.put("type", "error");
                    errorEvent.put("message", "提问次数已用完，请注册后继续");
                    errorEmitter.send(errorEvent.toJSONString());
                } catch (Exception ignored) {}
                errorEmitter.complete();
                return errorEmitter;
            }
        } else {
            currentUserId = BaseContext.getCurrentId();
        }

        // 提取为final变量，供lambda表达式使用
        final Integer finalUserId = currentUserId;
        final Integer finalGuestId = currentGuestId;

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
                // 获取会话历史
                List<ConversationHistory> history = aiConsultService.getConversationHistory(sessionId);
                Integer turnNumber = history.size() / 2 + 1;


                PythonRequest request = PythonRequest.builder()
                        .userId(finalUserId)
                        .question(question)
                        .sessionId(sessionId)
                        .conversationHistory(history)
                        .turnNumber(turnNumber)
                        .build();

                // 流式调用 Python 服务，逐个转发 SSE 事件
                HttpClient.doPostJsonStreaming(STREAM_URL, request, eventData -> {
                    try {
                        JSONObject event = JSONObject.parseObject(eventData);
                        String type = event.getString("type");

                        if ("status".equals(type) || "progress".equals(type) || "token".equals(type)) {
                            // 转发状态、进度、token 事件给前端
                            emitter.send(eventData);
                        } else if ("complete".equals(type)) {
                            // 转换 data_cards 为前端期望的嵌套结构
                            JSONArray rawCards = event.getJSONArray("data_cards");
                            JSONArray transformedCards = transformDataCards(rawCards);
                            event.put("data_cards", transformedCards);

                            // 转发转换后的 complete 事件给前端
                            emitter.send(event.toJSONString());

                            // 保存会话到数据库和 Redis
                            saveConsultation(question, sessionId, event, turnNumber, finalUserId, finalGuestId, userType);
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
                log.error("流式 AI 咨询失败", e);
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
     * 保存咨询记录到数据库和 Redis
     */
    private void saveConsultation(String question, String sessionId, JSONObject completeEvent, Integer turnNumber, Integer userId, Integer guestId, String userType) {
        try {
            String answer = completeEvent.getString("answer");
            JSONArray dataCards = completeEvent.getJSONArray("data_cards");
            String dataCardsJson = dataCards != null ? dataCards.toJSONString() : "[]";

            if ("guest".equals(userType)) {
                GuestConsultation gc = GuestConsultation.builder()
                        .sessionId(sessionId)
                        .turnNumber(turnNumber)
                        .guestId(guestId)
                        .question(question)
                        .answer(answer)
                        .dataCards(dataCardsJson)
                        .createTime(new java.util.Date())
                        .build();
                aiConsultService.saveGuestConsultationDirect(gc);
                guestFeignClient.incrementCount(guestId);
            } else {
                AiConsultation consultation = AiConsultation.builder()
                        .sessionId(sessionId)
                        .turnNumber(turnNumber)
                        .userId(userId)
                        .question(question)
                        .answer(answer)
                        .dataCards(dataCardsJson)
                        .createTime(new java.util.Date())
                        .build();
                aiConsultService.saveConsultationDirect(consultation);
            }
            log.info("流式咨询记录已保存: sessionId={}, turnNumber={}", sessionId, turnNumber);
        } catch (Exception e) {
            log.error("保存流式咨询记录失败", e);
        }
    }

    /**
     * 将 Python 返回的扁平 data_cards 转换为前端期望的嵌套结构
     * 与 AIConsultServiceImpl.parsePythonResult() 中的逻辑保持一致
     */
    private JSONArray transformDataCards(JSONArray dataCards) {
        if (dataCards == null || dataCards.isEmpty()) {
            return new JSONArray();
        }
        JSONArray transformed = new JSONArray();
        for (int i = 0; i < dataCards.size(); i++) {
            JSONObject card = dataCards.getJSONObject(i);
            String type = card.getString("type");
            Float relevance = card.getFloat("relevance");

            JSONObject transformedCard = new JSONObject();
            transformedCard.put("type", type);
            transformedCard.put("relevance", relevance);

            if ("law_article".equals(type)) {
                Long id = card.getLong("id");
                //通过Feign调用law-law-service获取法律条文
                LawArticle lawArticle = lawServiceFeignClient.getLawArticle(id).getData();
                if (lawArticle != null) {
                    transformedCard.put("lawArticle", lawArticle);
                }
            } else if ("law_case".equals(type)) {
                Long id = card.getLong("id");
                //通过Feign调用law-law-service获取案例卡片
                LawCaseVO lawCaseVO = lawServiceFeignClient.getLawCaseCard(id).getData();
                if (lawCaseVO != null) {
                    transformedCard.put("lawCaseVO", lawCaseVO);
                }
            } else if ("consult_history".equals(type)) {
                Integer id = card.getInteger("id");
                AiConsultation consultation = aiConsultationMapper.get(id);
                if (consultation != null) {
                    transformedCard.put("aiConsultation", consultation);
                }
            }
            transformed.add(transformedCard);
        }
        return transformed;
    }

    @PostMapping ("/createSession")
    public Result createSession(@RequestBody AiConsultDTO aiConsultDTO){
        aiConsultService.createSession(aiConsultDTO.getSessionId());
        return Result.success();
    }
    @GetMapping("/history")
    public Result<List<AiSessionHistoryVO>> history(){
        log.info("history");
        return Result.success(aiConsultService.AllSession());
    }
    @GetMapping("/chatDetail")
    public Result<List<AiConsultationDetailVO>> chatDetail(@RequestParam String sessionId){
        log.info("sessionId:{}",sessionId);
        return Result.success(aiConsultService.chatDetail(sessionId));
    }
    @DeleteMapping("/deleteSession")
    public Result deleteSession(@RequestParam String sessionId){
        log.info("sessionId:{}",sessionId);
        aiConsultService.deleteSession(sessionId);
        return Result.success();
    }

    @GetMapping("/guest/history")
    public Result<List<AiSessionHistoryVO>> guestHistory(){
        Integer guestId = BaseContext.getCurrentGuestId();
        log.info("guest history: guestId={}", guestId);
        return Result.success(guestConsultationMapper.getAllGuestSession(guestId));
    }

    @GetMapping("/guest/chatDetail")
    public Result<List<AiConsultationDetailVO>> guestChatDetail(@RequestParam String sessionId){
        log.info("guest chatDetail: sessionId={}", sessionId);
        List<AiConsultationDetailVO> list = guestConsultationMapper.guestChatDetail(sessionId);
        for (AiConsultationDetailVO vo : list) {
            vo.setDataCards(JSON.parseArray(vo.getDataCardsJson(), Object.class));
            vo.setDataCardsJson(null);
        }
        return Result.success(list);
    }

    @DeleteMapping("/guest/deleteSession")
    public Result deleteGuestSession(@RequestParam String sessionId){
        log.info("delete guest session: sessionId={}", sessionId);
        guestConsultationMapper.deleteGuestSession(sessionId);
        return Result.success();
    }

    @PostMapping("/guest/createSession")
    public Result createGuestSession(@RequestParam String sessionId){
        log.info("create guest session: sessionId={}", sessionId);
        return Result.success();
    }

    @PostMapping("/guest/merge")
    public Result mergeGuest(@RequestParam String guestKey) {
        Integer userId = BaseContext.getCurrentId();
        log.info("游客数据迁移: guestKey={}, userId={}", guestKey, userId);

        Result<GuestInfoVO> guestInfoResult = guestFeignClient.getGuestInfo(guestKey);
        if (guestInfoResult.getData() == null) {
            return Result.error("游客信息不存在");
        }
        Integer guestId = guestInfoResult.getData().getGuestId();

        aiConsultService.mergeGuestData(guestId, userId);

        guestFeignClient.deleteGuest(guestId);

        return Result.success();
    }

}
