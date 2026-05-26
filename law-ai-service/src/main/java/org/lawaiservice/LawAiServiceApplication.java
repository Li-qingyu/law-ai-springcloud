package org.lawaiservice;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.scheduling.annotation.EnableAsync;

@EnableDiscoveryClient
@EnableFeignClients
@SpringBootApplication
@EnableAsync
@MapperScan("org.lawaiservice.mapper")
public class LawAiServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(LawAiServiceApplication.class, args);
    }

}
