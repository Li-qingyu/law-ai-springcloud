package org.lawaiservice.service;

import org.lawaiservice.client.AiConsultResponse;
import org.lawcommoncore.entity.AiConsultation;
import org.lawcommoncore.entity.ConversationHistory;
import org.lawcommoncore.vo.AiConsultationDetailVO;
import org.lawcommoncore.vo.AiSessionHistoryVO;

import java.util.List;

public interface AIConsultService {
    AiConsultResponse consult(String question, String sessionId);

    void createSession(String sessionId);

    List<AiSessionHistoryVO> AllSession();

    List<AiConsultationDetailVO> chatDetail(String sessionId);

    void deleteSession(String sessionId);

    List<ConversationHistory> getConversationHistory(String sessionId);

    void saveConsultationDirect(AiConsultation consultation);
}
