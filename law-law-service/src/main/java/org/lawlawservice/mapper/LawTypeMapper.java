package org.lawlawservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.lawcommoncore.dto.TypeDTO;
import org.lawcommoncore.entity.LawType;
import org.lawcommoncore.vo.LawTypeListVO;

import java.util.List;

@Mapper
public interface LawTypeMapper {
    LawType get(Long id);

    List<LawTypeListVO> list(String  name);

    void insert(TypeDTO typeDTO);

    void update(TypeDTO typeDTO);

    void delete(Long id);

    List<LawType> all();
    @Select("select count(1) from law_type")
    Integer count();
    @Select("select count(*) from law_type where create_time < DATE_SUB(NOW(),  INTERVAL 7 DAY)")
    Integer countOneWeekAgo();
}
