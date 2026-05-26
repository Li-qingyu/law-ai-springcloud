package org.lawcommonservice.service.Impl;

import org.lawcommoncore.entity.StatisticItem;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.WorkSpaceVO;
import org.lawcommonservice.feign.LawFeignClient;
import org.lawcommonservice.feign.UserFeignClient;
import org.lawcommonservice.service.WorkSpaceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class WorkSpaceServiceImpl implements WorkSpaceService {
    @Autowired
    private LawFeignClient lawFeignClient;
    @Autowired
    private UserFeignClient userFeignClient;

    @Override
    public WorkSpaceVO trend() {
        Integer currentCase = lawFeignClient.getCaseCount().getData();
        Integer currentType = lawFeignClient.getTypeCount().getData();
        Integer currentArticle = lawFeignClient.getArticleCount().getData();
        Integer currentUser = userFeignClient.getUserCount().getData();

        Integer oldCase = lawFeignClient.getCaseCountOneWeekAgo().getData();
        Integer oldType = lawFeignClient.getTypeCountOneWeekAgo().getData();
        Integer oldArticle = lawFeignClient.getArticleCountOneWeekAgo().getData();
        Integer oldUser = userFeignClient.getUserCountOneWeekAgo().getData();

        return new WorkSpaceVO(
                new StatisticItem(currentCase, calculateTrend(currentCase, oldCase)),
                new StatisticItem(currentType, calculateTrend(currentType, oldType)),
                new StatisticItem(currentArticle, calculateTrend(currentArticle, oldArticle)),
                new StatisticItem(currentUser, calculateTrend(currentUser, oldUser))
        );
    }

    private Double calculateTrend(Integer current, Integer old) {
        if (old == null || old == 0) {
            return current != null && current > 0 ? 100.0 : 0.0;
        }
        double trend = ((current - old) * 100.0) / old;
        return Math.round(trend * 100.0) / 100.0;
    }
}
