package org.lawlawservice.listener;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.event.LawArticleSyncEvent;
import org.lawlawservice.feign.MilvusFeignClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
@Slf4j
public class LawArticleSyncListener {
    @Autowired
    private MilvusFeignClient milvusFeignClient;

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleLawArticleEvent(LawArticleSyncEvent event) {
        log.info("接受法律同步事件: {}", event);
        try{
            switch (event.getSyncType()) {
                case ADD, UPDATE:
                    milvusFeignClient.addLawArticle(event.getLawArticle());
                    break;
                case DELETE:
                    if (event.getIds() != null && !event.getIds().isEmpty()) {
                        milvusFeignClient.deleteLawArticles(event.getIds());
                    }
                    break;
            }
        }catch (Exception e){
            log.error("法律条文同步到Milvus失败: type={}, id={}, ids={}, error={}",
                    event.getSyncType(),
                    event.getLawArticle() != null ? event.getLawArticle().getId() : null,
                    event.getIds(),
                    e.getMessage(), e);
        }

    }
}
