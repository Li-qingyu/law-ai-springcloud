package org.lawcommonservice.controller;

import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.CarouselVO;
import org.lawcommonservice.service.CarouselService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class CarouselController {
    @Autowired
    private CarouselService carouselService;

    @GetMapping("/user/home/carousel")
    public Result<List<CarouselVO>> list() {
        return Result.success(carouselService.list());
    }

}
