package org.lawcommonsecurity.aspect;

import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.lawcommoncore.annotation.RecordActivity;
import org.lawcommoncore.context.BaseContext;
import org.lawcommonsecurity.service.ActivityService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.expression.Expression;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.StandardEvaluationContext;
import org.springframework.stereotype.Component;

@Aspect
@Component
@Slf4j
public class ActivityAspect {
    @Autowired
    private ActivityService activityService;

    @AfterReturning("@annotation(recordActivity)")
    public void recordActivity(JoinPoint joinPoint, RecordActivity recordActivity) {
        log.info("AOP拦截");
        Integer userId = BaseContext.getCurrentId();
        if (userId == null) {
            log.warn("用户未登录");
            return;
        }
        try {
            String type = recordActivity.type();
            String titleTemplate = recordActivity.titleTemplate();
            String title = parseTitleTemplate(titleTemplate, joinPoint);
            activityService.add(userId, type, title);
        } catch (Exception e) {
            log.error("记录用户行为失败");
            e.printStackTrace();
        }
    }

    private String parseTitleTemplate(String titleTemplate, JoinPoint joinPoint) {
        Object[] args = joinPoint.getArgs();
        MethodSignature methodSignature = (MethodSignature) joinPoint.getSignature();
        String[] paramNames = methodSignature.getParameterNames();

        StandardEvaluationContext context = new StandardEvaluationContext();
        for (int i = 0; i < paramNames.length; i++) {
            context.setVariable(paramNames[i], args[i]);
        }

        ExpressionParser parser = new SpelExpressionParser();
        Expression expression = parser.parseExpression(titleTemplate);

        return expression.getValue(context, String.class);
    }
}
