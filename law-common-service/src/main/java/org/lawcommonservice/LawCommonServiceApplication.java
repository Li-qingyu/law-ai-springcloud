package org.lawcommonservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class LawCommonServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(LawCommonServiceApplication.class, args);
    }

}
