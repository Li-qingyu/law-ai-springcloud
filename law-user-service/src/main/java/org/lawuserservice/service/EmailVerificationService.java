package org.lawuserservice.service;

public interface EmailVerificationService {
    
    /**
     * 发送验证码邮件
     * @param email 收件人邮箱
     * @return 发送结果信息
     */
    String sendVerificationCode(String email);
    
    /**
     * 验证验证码是否正确
     * @param email 邮箱
     * @param code 验证码
     * @return 验证结果
     */
    boolean verifyCode(String email, String code);
}