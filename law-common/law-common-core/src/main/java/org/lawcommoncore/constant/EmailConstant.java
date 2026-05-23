package org.lawcommoncore.constant;

public class EmailConstant {
    
    // Redis key 前缀
    public static final String EMAIL_CODE_PREFIX = "email_code:";
    public static final String EMAIL_SEND_TIME_PREFIX = "email_send_time:";
    
    // 验证码有效期（秒）- 5 分钟
    public static final int CODE_EXPIRE_TIME = 180;
    
    // 发送间隔时间（秒）- 1 分钟
    public static final int SEND_INTERVAL_TIME = 60;
    
    // 验证码长度
    public static final int CODE_LENGTH = 4;
    
    // 邮件标题
    public static final String EMAIL_SUBJECT = "【法律咨询平台】您的验证码";
}
