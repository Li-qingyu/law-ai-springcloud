package org.lawcommonsecurity.config;

import lombok.extern.slf4j.Slf4j;
import org.lawcommonsecurity.interceptor.JwtTokenInterceptor;
import org.lawcommonsecurity.properties.JwtProperties;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Slf4j
@Configuration
@ComponentScan(basePackages = "org.lawcommonsecurity")
@MapperScan("org.lawcommonsecurity.mapper")
@EnableConfigurationProperties(JwtProperties.class)
public class SecurityAutoConfiguration implements WebMvcConfigurer {

    @Autowired
    private JwtTokenInterceptor jwtTokenInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        log.info("注册JWT令牌校验拦截器");
        registry.addInterceptor(jwtTokenInterceptor)
                .addPathPatterns("/**")
                .excludePathPatterns(
                        "/login",
                        "/register",
                        "/sendEmailCode",
                        "/upload/**",
                        "/test/public",
                        "/resetPassword",
                        "/guest/init"
                );
    }
}
