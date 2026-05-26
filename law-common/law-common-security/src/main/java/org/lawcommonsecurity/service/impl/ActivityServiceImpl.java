package org.lawcommonsecurity.service.impl;

import org.lawcommoncore.entity.Activities;
import org.lawcommoncore.entity.DeleteInfo;
import org.lawcommoncore.vo.ActivitiesVO;
import org.lawcommonsecurity.mapper.ActivitiesMapper;
import org.lawcommonsecurity.service.ActivityService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class ActivityServiceImpl implements ActivityService {

    @Autowired
    private ActivitiesMapper activitiesMapper;

    @Override
    public void add(Integer userId, String type, String title) {
        Activities activities = Activities.builder()
                .userId(userId)
                .type(type)
                .title(title)
                .time(LocalDateTime.now())
                .build();
        activitiesMapper.insert(activities);
    }

    @Override
    public List<ActivitiesVO> queryRecentActivities(int i) {
        return activitiesMapper.queryRecentActivities(i);
    }

    @Override
    public void delete(DeleteInfo deleteInfo) {
        activitiesMapper.delete(deleteInfo);
    }
}
