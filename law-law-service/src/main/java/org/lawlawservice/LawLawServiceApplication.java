package org.lawlawservice;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@MapperScan("org.lawlawservice.mapper")
public class LawLawServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(LawLawServiceApplication.class, args);
    }

}
