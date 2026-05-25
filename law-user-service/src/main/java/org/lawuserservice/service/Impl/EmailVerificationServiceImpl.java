package org.lawuserservice.service.Impl;

import jakarta.mail.internet.MimeMessage;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.constant.EmailConstant;
import org.lawuserservice.exception.RegisterException;
import org.lawuserservice.mapper.UserMapper;
import org.lawuserservice.service.EmailVerificationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.util.Random;
import java.util.concurrent.TimeUnit;
@Slf4j
@Service
public class EmailVerificationServiceImpl implements EmailVerificationService {

    @Autowired
    private JavaMailSender mailSender;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private UserMapper userMapper;

    @Override
    public String sendVerificationCode(String email) {
        try {
            // 校验邮箱格式
            if (!isValidEmail(email)) {
                throw new RegisterException("邮箱格式不正确");
            }

            // 检查是否在发送冷却期内
            String sendTimeKey = EmailConstant.EMAIL_SEND_TIME_PREFIX + email;
            Boolean hasSent = redisTemplate.hasKey(sendTimeKey);
            if (hasSent != null && hasSent) {
                return "发送过于频繁，请 3 分钟后再试";
            }

            // 生成 4 位数字验证码
            String code = generateCode();

            // 存储验证码到 Redis
            String codeKey = EmailConstant.EMAIL_CODE_PREFIX + email;
            redisTemplate.opsForValue().set(codeKey, code, EmailConstant.CODE_EXPIRE_TIME, TimeUnit.SECONDS);

            // 存储发送时间到 Redis
            redisTemplate.opsForValue().set(sendTimeKey, String.valueOf(System.currentTimeMillis()), 
                    EmailConstant.SEND_INTERVAL_TIME, TimeUnit.SECONDS);
            log.info("已发送验证码给邮箱：" + email);
            log.info("已存储验证码到 Redis：" + code);
            // 构建并发送邮件
            sendEmail(email, code);

            return "验证码发送成功";
        } catch (Exception e) {
            return "发送失败：" + e.getMessage();
        }
    }

    @Override
    public boolean verifyCode(String email, String code) {
        String codeKey = EmailConstant.EMAIL_CODE_PREFIX + email;
        String storedCode = redisTemplate.opsForValue().get(codeKey);
        
        if (storedCode == null) {
            return false;
        }
        
        boolean isValid = storedCode.equals(code);
        
        // 验证成功后删除验证码（防止重复使用）
        if (isValid) {
            redisTemplate.delete(codeKey);
        }
        
        return isValid;
    }

    /**
     * 生成 4 位数字验证码
     */
    private String generateCode() {
        Random random = new Random();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < EmailConstant.CODE_LENGTH; i++) {
            sb.append(random.nextInt(10));
        }
        return sb.toString();
    }

    /**
     * 校验邮箱格式
     */
    private boolean isValidEmail(String email) {
        String regex = "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$";
        return email != null && email.matches(regex);
    }

    /**
     * 发送邮件
     */
    private void sendEmail(String email, String code) throws Exception {
        MimeMessage message = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
        
        helper.setFrom("1325895727@qq.com");
        helper.setTo(email);
        helper.setSubject(EmailConstant.EMAIL_SUBJECT);
        
        // HTML 格式的邮件内容
        String htmlContent = buildEmailHtml(code);
        helper.setText(htmlContent, true);
        
        mailSender.send(message);
    }

    /**
     * 构建 HTML 邮件内容
     */
    private String buildEmailHtml(String code) {
        return "<!DOCTYPE html>" +
                "<html>" +
                "<head>" +
                "<meta charset='UTF-8'>" +
                "<style>" +
                "body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }" +
                ".container { max-width: 600px; margin: 0 auto; padding: 20px; }" +
                ".header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }" +
                ".content { padding: 30px; background-color: #f9f9f9; }" +
                ".code-box { background-color: #fff; border: 2px dashed #4CAF50; padding: 20px; " +
                "text-align: center; font-size: 32px; font-weight: bold; color: #4CAF50; margin: 20px 0; }" +
                ".footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }" +
                "</style>" +
                "</head>" +
                "<body>" +
                "<div class='container'>" +
                "<div class='header'><h1>法律咨询平台</h1></div>" +
                "<div class='content'>" +
                "<p>尊敬的客户：</p>" +
                "<p>您好！您正在进行注册/登录验证。</p>" +
                "<div class='code-box'>" + code + "</div>" +
                "<p><strong>有效期：5 分钟</strong></p>" +
                "<p>请勿将验证码泄露给他人。如非本人操作，请忽略此邮件。</p>" +
                "</div>" +
                "<div class='footer'>" +
                "<p>—— 法律咨询平台</p>" +
                "<p>本邮件为系统自动发送，请勿回复</p>" +
                "</div>" +
                "</div>" +
                "</body>" +
                "</html>";
    }
}
