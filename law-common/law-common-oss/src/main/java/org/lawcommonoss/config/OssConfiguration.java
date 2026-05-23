package org.lawcommonoss.config;


import lombok.extern.slf4j.Slf4j;
import org.lawcommonoss.properties.AliOssProperties;
import org.lawcommonoss.utils.AliOssUtil;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

/**
 * 阿里云文件上传配置类
 */
@Configuration
@Slf4j
@ComponentScan(basePackages = "org.lawcommonoss")
@EnableConfigurationProperties(AliOssProperties.class)
public class OssConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public AliOssUtil aliOssUtil(AliOssProperties aliOssProperties){
        log.info("开始创建aliyun上传工具类:{}",aliOssProperties);
        return new AliOssUtil(aliOssProperties.getEndpoint(),
                aliOssProperties.getAccessKeyId(),
                aliOssProperties.getAccessKeySecret(),
                aliOssProperties.getBucketName());
    }
}
