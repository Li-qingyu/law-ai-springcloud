package org.lawcommonservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.result.Result;
import org.lawcommonoss.utils.AliOssUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@RestController
@RequestMapping("/upload")
public class UploadController {
    @Autowired
    private AliOssUtil aliyunOSSOperator;
    @PostMapping
    public Result upload(MultipartFile file) throws Exception {
        log.info("文件上传:{}",file.getOriginalFilename());
        String url =aliyunOSSOperator.upload(file.getBytes(), file.getOriginalFilename());
        log.info("文件上传的url：{}",url);

        return Result.success(url);
    }

}
