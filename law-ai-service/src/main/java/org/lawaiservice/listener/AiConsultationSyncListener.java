package org.lawaiservice.listener;

import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.service.MilvusSyncService;
import org.lawcommoncore.event.AiConsultationSyncEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;
@Slf4j
@Component
public class AiConsultationSyncListener {
    @Autowired
     private MilvusSyncService milvusSyncService;

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleAiConsultationEvent(AiConsultationSyncEvent event) {
        log.info("接受AI咨询同步事件: {}", event);
        try{
            switch (event.getSyncType()) {
                case ADD, UPDATE:
                    milvusSyncService.addConsultHistory(event.getAiConsultation());
                    break;
                case DELETE:
                    if (event.getIds() != null && !event.getIds().isEmpty()) {
                        milvusSyncService.deleteAiConsultation(event.getIds());
                    }
                    break;
            }
            log.info("AI咨询同步到Milvus成功: type={}, id={}, ids={}",
                    event.getSyncType(),
                    event.getAiConsultation() != null ? event.getAiConsultation().getId() : null,
                    event.getIds());
        }catch (Exception e){
            log.error("AI咨询同步到Milvus失败: type={}, id={}, ids={}, error={}",
                    event.getSyncType(),
                    event.getAiConsultation() != null ? event.getAiConsultation().getId() : null,
                    event.getIds(),
                    e.getMessage(), e);
        }
    }

}
