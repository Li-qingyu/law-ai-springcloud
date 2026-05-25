package org.lawlawservice.listener;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.event.LawCaseSyncEvent;
import org.lawlawservice.feign.MilvusFeignClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Slf4j
@Component
public class LawCaseSyncListener {
    @Autowired
    private MilvusFeignClient milvusFeignClient;

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleLawCaseEvent(LawCaseSyncEvent event) {
        log.info("接受案件同步事件: {}", event);
        try{
            switch (event.getSyncType()) {
                case ADD, UPDATE:
                    milvusFeignClient.addLawCase(event.getLawCase());
                    break;
                case DELETE:
                    if (event.getIds() != null && !event.getIds().isEmpty()) {
                        milvusFeignClient.deleteLawCases(event.getIds());
                    }
                    break;
            }
            log.info("案件同步到Milvus成功: type={}, id={}, ids={}",
                    event.getSyncType(),
                    event.getLawCase() != null ? event.getLawCase().getId() : null,
                    event.getIds());
        }catch (Exception e){
            log.error("案件同步到Milvus失败: type={}, id={}, ids={}, error={}",
                    event.getSyncType(),
                    event.getLawCase() != null ? event.getLawCase().getId() : null,
                    event.getIds(),
                    e.getMessage(), e);
        }
    }
}
