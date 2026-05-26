package org.lawcommonservice;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@MapperScan("org.lawcommonservice.mapper")
@EnableScheduling
public class LawCommonServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(LawCommonServiceApplication.class, args);
    }

}
