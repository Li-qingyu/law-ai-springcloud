package org.lawcommoncore.event;

import lombok.Getter;
import org.lawcommoncore.entity.LawCase;
import org.springframework.context.ApplicationEvent;

import java.util.List;
@Getter
public class LawCaseSyncEvent extends ApplicationEvent {
    private final List< Long> ids;
    private final LawCase lawCase;
    private final SyncType syncType;
    public enum SyncType {
        ADD, UPDATE, DELETE
    }
    public LawCaseSyncEvent(Object source, LawCase lawCase, SyncType syncType) {
        super(source);
        this.lawCase = lawCase;
        this.ids = null;
        this.syncType = syncType;
    }
    public LawCaseSyncEvent(Object source, List<Long> ids, SyncType syncType) {
        super(source);
        this.lawCase = null;
        this.ids = ids;
        this.syncType = syncType;
    }
}
