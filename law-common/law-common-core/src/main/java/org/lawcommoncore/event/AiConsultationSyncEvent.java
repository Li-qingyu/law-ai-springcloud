package org.lawcommoncore.event;

import lombok.Getter;
import org.lawcommoncore.entity.AiConsultation;
import org.springframework.context.ApplicationEvent;

import java.util.List;
@Getter
public class AiConsultationSyncEvent extends ApplicationEvent {
    private final List< String> ids;
    private final AiConsultation aiConsultation;
    private final SyncType syncType;

    public enum SyncType {
        ADD, UPDATE, DELETE
    }
    public AiConsultationSyncEvent(Object source, AiConsultation aiConsultation, SyncType syncType) {
        super(source);
        this.aiConsultation = aiConsultation;
        this.ids = null;
        this.syncType = syncType;
    }
    public AiConsultationSyncEvent(Object source, List< String> ids, SyncType syncType) {
        super(source);
        this.aiConsultation = null;
        this.ids = ids;
        this.syncType = syncType;
    }

}
