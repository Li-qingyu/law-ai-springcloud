package org.lawaiservice;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableDiscoveryClient
@EnableFeignClients
@SpringBootApplication
@EnableAsync
@EnableScheduling
@MapperScan("org.lawaiservice.mapper")
public class LawAiServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(LawAiServiceApplication.class, args);
    }

}
