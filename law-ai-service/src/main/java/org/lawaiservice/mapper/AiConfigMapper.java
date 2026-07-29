package org.lawaiservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.AiConfig;

import java.util.List;

@Mapper
public interface AiConfigMapper {

    List<AiConfig> selectList();

    AiConfig selectById(Integer id);

    AiConfig selectDefault();

    AiConfig selectByProvider(@Param("provider") String provider);

    int insert(AiConfig aiConfig);

    int updateById(AiConfig aiConfig);

    int deleteById(Integer id);

    int clearDefault();

    int setDefault(Integer id);
}
