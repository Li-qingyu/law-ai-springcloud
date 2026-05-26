package org.lawcommonservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.ActivitiesVO;
import org.lawcommoncore.vo.WorkSpaceVO;
import org.lawcommonsecurity.service.ActivityService;
import org.lawcommonservice.service.WorkSpaceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@Slf4j
@RequestMapping("/admin")
public class WorkSpcaeController {
    @Autowired
    private WorkSpaceService workSpaceService;
    @Autowired
    private ActivityService activityService;
    /**
     * 处理增长趋势
     */
    @GetMapping("/work-space/trend")
    public Result trend() {
        log.info("处理增长趋势");
         WorkSpaceVO workSpaceVO =workSpaceService.trend();
        return Result.success(workSpaceVO);
    }
    /**
     * 查询最近活动
     */
    @GetMapping("/dashboard/activities")
    public Result<List<ActivitiesVO>> activities(){
        log.info("查询最近活动");
        List<ActivitiesVO> activities =activityService.queryRecentActivities(8);
        return Result.success(activities);
    }

}
