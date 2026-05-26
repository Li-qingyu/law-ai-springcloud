package org.lawlawservice.service.Impl;

import org.lawcommoncore.annotation.RecordActivity;
import org.lawcommoncore.dto.TypeDTO;
import org.lawcommoncore.entity.LawType;
import org.lawcommoncore.vo.LawTypeListVO;
import org.lawlawservice.exception.LawTypeException;
import org.lawlawservice.mapper.LawTypeMapper;
import org.lawlawservice.service.LawTypeService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

import static org.lawcommoncore.constant.ActivitiesConstant.*;

@Service
public class LawTypeServiceImpl implements LawTypeService {
    @Autowired
    private LawTypeMapper lawTypeMapper;

    @Override
    public LawType get(Long id) {
        if(id == null){
            throw new LawTypeException("id不能为空");
        }
        return lawTypeMapper.get(id);
    }

    @Override
    public List<LawTypeListVO> list(String name) {
        return lawTypeMapper.list(name);
    }
    @RecordActivity(type = TYPE_ADD, titleTemplate = "'添加法律类型：' + #typeDTO.name")
    @Override
    public void add(TypeDTO typeDTO) {
        if(typeDTO == null){
            throw new LawTypeException("法律类型不能为空");
        }
        LawType lawType = new LawType();
        BeanUtils.copyProperties(typeDTO,lawType);
        lawType.setCreateTime(LocalDateTime.now());
        lawType.setUpdateTime(LocalDateTime.now());
        lawTypeMapper.insert(typeDTO);
    }
    @RecordActivity(type = TYPE_UPDATE, titleTemplate = "'更新法律类型：' + #typeDTO.name")
    @Override
    public void updateLawType(TypeDTO typeDTO) {
        if(typeDTO == null)
            throw new LawTypeException("法律类型不能为空");
        LawType lawType = new LawType();
        //把第一个参数的属性中与第二个参数相同的属性复制到第二个属性上
        BeanUtils.copyProperties(typeDTO,lawType);
        lawType.setUpdateTime(LocalDateTime.now());
        lawTypeMapper.update(typeDTO);
    }
    @RecordActivity(type = TYPE_DELETE, titleTemplate = "'删除法律类型：' + #id")
    @Override
    public void delete(Long id) {
        if(id == null)
            throw new LawTypeException("id不能为空");
        lawTypeMapper.delete(id);
    }

    @Override
    public List<LawType> list() {
        return lawTypeMapper.all();
    }

    @Override
    public Integer count() {
        return lawTypeMapper.count();
    }

    @Override
    public Integer countOneWeekAgo() {
        return lawTypeMapper.countOneWeekAgo();
    }
}
