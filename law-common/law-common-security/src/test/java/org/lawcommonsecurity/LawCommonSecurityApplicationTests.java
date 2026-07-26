package org.lawcommonsecurity;

import io.jsonwebtoken.Claims;
import org.junit.jupiter.api.Test;
import org.lawcommonsecurity.properties.JwtProperties;
import org.lawcommonsecurity.utils.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class LawCommonSecurityApplicationTests {
    @Autowired
    private JwtProperties jwtProperties;

    @Autowired
    private JwtUtil jwtUtil;

    @Test
    void contextLoads() {

    }

}
