package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class DailyTokenStatsVO implements Serializable {
    private List<DailyTokenUsageVO> last7Days;
    private List<DailyTokenUsageVO> last30Days;
}
