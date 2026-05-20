package org.lawgateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class LawGatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(LawGatewayApplication.class, args);
    }

}
