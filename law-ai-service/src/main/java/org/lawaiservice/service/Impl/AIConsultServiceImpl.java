package org.lawaiservice.service.Impl;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.client.AiConsultResponse;
import org.lawaiservice.client.ClientState;
import org.lawaiservice.client.PythonRequest;
import org.lawaiservice.feign.LawServiceFeignClient;
import org.lawaiservice.mapper.AiConsultationMapper;
import org.lawaiservice.service.AIConsultService;
import org.lawaiservice.utils.HttpClient;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.data_card.ConsultHistoryDataCard;
import org.lawcommoncore.data_card.LawArticleDataCard;
import org.lawcommoncore.data_card.LawCaseDataCard;
import org.lawcommoncore.entity.AiConsultation;
import org.lawcommoncore.entity.ConversationHistory;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.event.AiConsultationSyncEvent;
import org.lawcommoncore.vo.AiConsultationDetailVO;
import org.lawcommoncore.vo.AiSessionHistoryVO;
import org.lawcommoncore.vo.LawCaseVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
@Slf4j
public class AIConsultServiceImpl implements AIConsultService {
    @Autowired
    private AiConsultationMapper aiConsultationMapper;
    @Autowired
    private StringRedisTemplate redisTemplate;
    @Autowired
    private LawServiceFeignClient lawServiceFeignClient;

    @Autowired
    private ApplicationEventPublisher eventPublisher;



    private static final String url="http://localhost:8000/v1/ai/consult";
    private static final String SESSION_KEY_PREFIX = "ai:session:";
    private static final long SESSION_TTL_HOURS = 12;
    private static final int MAX_HISTORY_ROUNDS = 5;

    @Transactional(rollbackFor = Exception.class)
    @Override
    public AiConsultResponse consult(String question, String sessionId) {
        log.info("ai咨询：{},{}" , question, sessionId);
        //redis中获取内容
        String key=SESSION_KEY_PREFIX+sessionId;
        String json=redisTemplate.opsForValue().get(key);
        if(json!=null){
            List<ConversationHistory> history=getConversationHistory(sessionId);
            Integer turnNumber=history.size()/2+1;
            PythonRequest request=PythonRequest.builder()
                    .userId(BaseContext.getCurrentId())
                    .question(question)
                    .sessionId(sessionId)
                    .conversationHistory(history)
                    .turnNumber(turnNumber)
                    .build();
            try{
                //调用 python服务
                String response= HttpClient.doPostJson(url,request);
                AiConsultResponse aiConsultResponse=parsePythonResult(response);
                                
                // 将 data_cards 转换为 JSON 字符串
                String dataCardsJson = JSON.toJSONString(aiConsultResponse.getData_cards());
                                
                //MySQL保存会话历史
                AiConsultation consultation=AiConsultation.builder()
                        .sessionId(sessionId)
                        .turnNumber(turnNumber)
                        .userId(BaseContext.getCurrentId())
                        .question(question)
                        .answer(aiConsultResponse.getAnswer())
                        .dataCards(dataCardsJson)
                        .createTime(new java.util.Date())
                        .build();
                aiConsultationMapper.insert(consultation);

                eventPublisher.publishEvent(new AiConsultationSyncEvent(this, consultation, AiConsultationSyncEvent.SyncType.ADD));

                //更新redis
                updateHistoryToRedis(sessionId, question,aiConsultResponse.getAnswer(), turnNumber);
                return aiConsultResponse;
            }catch (IOException e){
                log.error("调用python服务失败",e);
                throw new RuntimeException("调用python服务失败");
            }

        }


        return null;
    }

    // 获取会话历史
    @Override
    public List<ConversationHistory> getConversationHistory(String sessionId) {
        //redis
        String key=SESSION_KEY_PREFIX+sessionId;
        String json=redisTemplate.opsForValue().get(key);
        if(json==null|| json.isEmpty()){
            return new ArrayList<>();
        }
        try{
            List<ConversationHistory> history=JSONObject.parseArray(json,ConversationHistory.class);
            int maxRecords = MAX_HISTORY_ROUNDS * 2;
            if (history.size() > maxRecords) {
                history = new ArrayList<>(history.subList(history.size() - maxRecords, history.size()));
            }
            return history;
        }catch (Exception e){
            log.error("获取会话历史失败",e);
            return new ArrayList<>();
        }

    }
    // 解析python返回结果
    private AiConsultResponse parsePythonResult(String result) {
        JSONObject responseData = JSONObject.parseObject(result);
        ClientState clientState = new ClientState(responseData.getString("status"), responseData.getJSONObject("data"), responseData.getString("message"));
        if (!clientState.getStatus().equals("success")) {
            log.error("python返回结果错误：{}", clientState.getMessage());
            throw new RuntimeException("python返回结果错误");
        }
        Map<String, Object> data = clientState.getData();
        AiConsultResponse aiConsultResponse = AiConsultResponse.builder()
                .answer(data.get("answer").toString())
                .session_id(data.get("session_id").toString())
                .turn_number(Integer.parseInt(data.get("turn_number").toString()))
                .user_id(Integer.parseInt(data.get("user_id").toString()))
                .data_cards(new ArrayList<>())
                .build();
        JSONArray data_cards=responseData.getJSONObject("data").getJSONArray("data_cards");
        for (int i = 0; i < data_cards.size(); i++) {
            JSONObject data_card = data_cards.getJSONObject(i);
            String type = data_card.getString("type");
            Float scope=data_card.getFloat("relevance");
            if (type.equals("law_article")) {

                Long id = data_card.getLong("id");
                //通过Feign调用law-law-service获取法律条文
                LawArticle lawArticle = lawServiceFeignClient.getLawArticle(id).getData();
                LawArticleDataCard lawArticleDataCard = LawArticleDataCard.builder()
                        .type(type)
                        .lawArticle(lawArticle)
                        .relevance(scope)
                        .build();
                aiConsultResponse.getData_cards().add(lawArticleDataCard);
            }else if(type.equals("law_case")){

                Long id = data_card.getLong("id");
                //通过Feign调用law-law-service获取案例卡片
                LawCaseVO lawCaseVO = lawServiceFeignClient.getLawCaseCard(id).getData();
                LawCaseDataCard lawCaseDataCard = LawCaseDataCard.builder()
                        .type(type)
                        .lawCaseVO(lawCaseVO)
                        .relevance(scope)
                        .build();
                aiConsultResponse.getData_cards().add(lawCaseDataCard);
            }else if(type.equals("consult_history")){
                AiConsultation consultation = new AiConsultation();
                consultation.setId(data_card.getInteger("id"));
                ConsultHistoryDataCard consultHistoryDataCard = ConsultHistoryDataCard.builder()
                        .type(type)
                        .aiConsultation(aiConsultationMapper.get(consultation.getId()))
                        .relevance(scope)
                        .build();
                aiConsultResponse.getData_cards().add(consultHistoryDataCard);
            }
            else{
                System.out.println("未知数据类型: " + type);
            }

        }
        return aiConsultResponse;
    }
    /**
     * 更新Redis会话历史
     */
    private void updateHistoryToRedis(String sessionId, String question, String answer, Integer turnNumber) {
        String key = SESSION_KEY_PREFIX + sessionId;

        // 获取现有历史
        List<ConversationHistory> history = getConversationHistory(sessionId);

        // 添加新的问答对
        LocalDateTime now = LocalDateTime.now();
        history.add(new ConversationHistory("user", question, now));
        history.add(new ConversationHistory("assistant", answer, now));

        // 限制历史记录长度（保留最近5轮，即10条消息）
        int maxRecords = MAX_HISTORY_ROUNDS * 2;
        if (history.size() > maxRecords) {
            history = new ArrayList<>(history.subList(history.size() - maxRecords, history.size()));
        }

        // 存回Redis
        String json = JSON.toJSONString(history);
        redisTemplate.opsForValue().set(key, json);
        redisTemplate.expire(key, SESSION_TTL_HOURS, TimeUnit.HOURS);

        log.info("更新会话历史: sessionId={}, turnNumber={}, historySize={}",
                sessionId, turnNumber, history.size());
    }
    /**
     * 清空会话历史
     */
    public void clearSession(String sessionId) {
        String key = SESSION_KEY_PREFIX + sessionId;
        redisTemplate.delete(key);
        log.info("清空会话: {}", sessionId);
    }

    @Override
    public void createSession(String sessionId) {
        log.info("创建session:{}", sessionId);
        //redis
        String key=SESSION_KEY_PREFIX+sessionId;
        redisTemplate.opsForValue().set(key,"[]");
        redisTemplate.expire(key, SESSION_TTL_HOURS, TimeUnit.HOURS);
    }

    @Override
    public List<AiSessionHistoryVO> AllSession() {
        log.info("获取所有会话");
        Integer userId=BaseContext.getCurrentId();
        return aiConsultationMapper.getAllSession(userId);

    }

    @Override
    public List<AiConsultationDetailVO> chatDetail(String sessionId) {
        List<AiConsultationDetailVO>  detailVOList=aiConsultationMapper.chatDetail(sessionId);
        for(AiConsultationDetailVO detailVO:detailVOList){
            detailVO.setDataCards(JSON.parseArray(detailVO.getDataCardsJson(),Object.class));
            detailVO.setDataCardsJson(null);
        }

        return detailVOList;
    }

    @Override
    public void deleteSession(String sessionId) {
        //删除redis的数据
        redisTemplate.delete(SESSION_KEY_PREFIX+sessionId);
        //删除数据库的数据
        aiConsultationMapper.delete(sessionId);
        //发布事件
        eventPublisher.publishEvent(new AiConsultationSyncEvent(this, List.of(sessionId), AiConsultationSyncEvent.SyncType.DELETE));

        log.info("删除session:{}", sessionId);
    }

    @Override
    public void saveConsultationDirect(AiConsultation consultation) {
        // 保存到 MySQL
        aiConsultationMapper.insert(consultation);

        // 更新 Redis 会话历史
        updateHistoryToRedis(
                consultation.getSessionId(),
                consultation.getQuestion(),
                consultation.getAnswer(),
                consultation.getTurnNumber()
        );

        log.info("直接保存咨询记录: sessionId={}, turnNumber={}",
                consultation.getSessionId(), consultation.getTurnNumber());
    }
}
