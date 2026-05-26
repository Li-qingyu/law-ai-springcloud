package org.lawcommonsecurity.service;

import org.lawcommoncore.entity.DeleteInfo;
import org.lawcommoncore.vo.ActivitiesVO;

import java.util.List;

public interface ActivityService {

    void add(Integer userId, String type, String title);

    List<ActivitiesVO> queryRecentActivities(int i);

    void delete(DeleteInfo deleteInfo);
}
