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

    /** 查询是否存在相同 (provider, model_name) 的配置，排除指定 id */
    int countByProviderModel(@Param("provider") String provider,
                             @Param("modelName") String modelName,
                             @Param("excludeId") Integer excludeId);

    /** 查询表中总配置数 */
    int countAll();
}
