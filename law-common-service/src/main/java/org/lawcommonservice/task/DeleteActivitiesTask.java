package org.lawcommonservice.task;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.entity.DeleteInfo;
import org.lawcommonsecurity.service.ActivityService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
@Slf4j
public class DeleteActivitiesTask {
    @Autowired
    private ActivityService activityService;
    @Scheduled(cron = "0 0 0 * * SUN")
    public void delete() {
        log.info("开始删除活动记录");
        //删除距离七天前的活动记录
        DeleteInfo deleteInfo = new DeleteInfo();
        deleteInfo.setTime(LocalDateTime.now().minusDays(7));
        activityService.delete(deleteInfo);
    }
}
