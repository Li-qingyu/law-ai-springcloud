import logging
from typing import List
from app.models.admin_log import AdminLog
from app.models.review_result import ReviewResult, ReviewIssue

logger = logging.getLogger(__name__)

class ReviewService:
    """审查服务"""

    def review(self, log: AdminLog) -> ReviewResult:
        """审查执行结果"""
        issues = []

        # 检查执行状态
        if log.status == "failed":
            issues.append(ReviewIssue(
                type="execution_error",
                description=f"执行失败: {log.error_message}",
                severity="high",
                suggestion="请检查输入参数和系统状态"
            ))

        # 检查执行时长
        if log.duration_ms and log.duration_ms > 5000:  # 超过5秒
            issues.append(ReviewIssue(
                type="performance_issue",
                description=f"执行时间过长: {log.duration_ms}ms",
                severity="medium",
                suggestion="请优化执行逻辑或检查系统负载"
            ))

        # 检查输入输出
        if log.input_data and not log.output_data:
            issues.append(ReviewIssue(
                type="missing_output",
                description="缺少输出数据",
                severity="medium",
                suggestion="请确保执行过程正确生成输出数据"
            ))

        # 生成整体评估
        if not issues:
            overall_assessment = "执行成功"
            requires_manual_review = False
        elif any(issue.severity == "high" for issue in issues):
            overall_assessment = "执行失败，需要人工审查"
            requires_manual_review = True
        else:
            overall_assessment = "执行完成，但存在问题"
            requires_manual_review = False

        return ReviewResult(
            task_id=log.task_id,
            agent_type=log.agent_type,
            issues=issues,
            overall_assessment=overall_assessment,
            requires_manual_review=requires_manual_review
        )
