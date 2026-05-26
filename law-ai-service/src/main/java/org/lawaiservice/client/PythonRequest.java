package org.lawaiservice.client;

import com.alibaba.fastjson.annotation.JSONField;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.lawcommoncore.entity.ConversationHistory;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PythonRequest {
    private String question;
    @JSONField(name = "user_id")
    private Integer userId;
    @JSONField(name = "turn_number")
    private Integer turnNumber;
    @JSONField(name = "session_id")
    private String sessionId;
    @JSONField(name = "conversation_history")
    private List<ConversationHistory> conversationHistory;
}
