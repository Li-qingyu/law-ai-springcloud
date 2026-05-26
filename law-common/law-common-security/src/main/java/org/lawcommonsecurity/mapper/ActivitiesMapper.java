package org.lawcommonsecurity.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.lawcommoncore.entity.Activities;
import org.lawcommoncore.entity.DeleteInfo;
import org.lawcommoncore.vo.ActivitiesVO;

import java.util.List;

@Mapper
public interface ActivitiesMapper {
    void insert(Activities activities);

    List<ActivitiesVO> queryRecentActivities(Integer limit);

    void delete(DeleteInfo deleteInfo);
}
