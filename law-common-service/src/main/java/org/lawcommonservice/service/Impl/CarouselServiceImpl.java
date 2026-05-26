package org.lawcommonservice.service.Impl;

import org.lawcommoncore.vo.CarouselVO;
import org.lawcommonservice.mapper.CarouselMapper;
import org.lawcommonservice.service.CarouselService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CarouselServiceImpl implements CarouselService {
    @Autowired
    private CarouselMapper carouselMapper;

    @Override
    public List<CarouselVO> list() {
        return carouselMapper.list();
    }
}
