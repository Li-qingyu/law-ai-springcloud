package org.lawcommoncore.exception;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.result.Result;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.yaml.snakeyaml.constructor.DuplicateKeyException;

import java.sql.SQLException;

/**
 * 全局异常处理器，处理项目中抛出的业务异常
 */
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    /**
     * 捕获业务异常
     * @param ex
     * @return
     */
    @ExceptionHandler
    public Result exceptionHandler(BaseException ex){
        log.error("异常信息：{}", ex.getMessage());
        return Result.error(ex.getMessage());
    }

    /**
     * 捕获数据库唯一键冲突异常
     */
    @ExceptionHandler
    public Result duplicateKeyExceptionHandler(DuplicateKeyException ex) {
        log.error("数据库唯一键冲突：{}", ex.getMessage());
        return Result.error("数据已存在，请勿重复添加");
    }


    /**
     * 捕获数据库 SQL 异常（如字段超长、唯一键冲突、非空约束等）
     * java.sql.SQLException 是 JDK 内置异常，无需额外依赖
     */
    @ExceptionHandler
    public Result sqlExceptionHandler(SQLException ex) {
        log.error("数据库异常：{}", ex.getMessage());
        String message = ex.getMessage();
        if (message != null) {
            if (message.contains("Data too long") || message.contains("data too long")) {
                return Result.error("字段值过长，请检查输入内容长度");
            }
            if (message.contains("cannot be null") || message.contains("Column cannot be null")) {
                return Result.error("必填字段不能为空");
            }
            if (message.contains("Duplicate entry") || message.contains("Duplicate")) {
                return Result.error("数据已存在，请勿重复添加");
            }
        }
        return Result.error("数据库操作异常：" + ex.getMessage());
    }


    /**
     * 捕获参数校验异常
     */
    @ExceptionHandler
    public Result illegalArgumentHandler(IllegalArgumentException ex) {
        log.error("参数异常：{}", ex.getMessage());
        return Result.error(ex.getMessage());
    }

    /**
     * 捕获角色授权失败异常，返回 HTTP 403
     */
    @ExceptionHandler
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public Result authorizationExceptionHandler(AuthorizationException ex) {
        log.warn("权限校验失败：{}", ex.getMessage());
        return Result.error(ex.getMessage());
    }

    /**
     * 捕获所有未预料的异常，兜底处理
     * 避免返回 HTTP 500 导致 Python AI 端无法解析错误信息
     */
    @ExceptionHandler
    public Result exceptionHandler(Exception ex){
        log.error("系统异常：", ex);
        return Result.error("系统内部错误：" + ex.getMessage());
    }


}
