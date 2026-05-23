package org.lawcommoncore.event;

import lombok.Getter;
import org.lawcommoncore.entity.LawArticle;
import org.springframework.context.ApplicationEvent;

import java.util.List;

@Getter
public class LawArticleSyncEvent extends ApplicationEvent {
    
    private final LawArticle lawArticle;
    private final SyncType syncType;
    private final List<Long> ids;
    
    public enum SyncType {
        ADD, UPDATE, DELETE
    }

    public LawArticleSyncEvent(Object source, LawArticle lawArticle, SyncType syncType) {
        super(source);
        this.lawArticle = lawArticle;
        this.ids = null;
        this.syncType = syncType;
    }

    public LawArticleSyncEvent(Object source, List<Long> ids, SyncType syncType) {
        super(source);
        this.lawArticle = null;
        this.ids = ids;
        this.syncType = syncType;
    }
}
