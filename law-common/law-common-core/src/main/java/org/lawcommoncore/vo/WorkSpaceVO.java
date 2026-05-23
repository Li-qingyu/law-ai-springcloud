package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.lawcommoncore.entity.StatisticItem;

import java.io.Serializable;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class WorkSpaceVO implements Serializable {
    private StatisticItem cases;
    private StatisticItem types;
    private StatisticItem articles;
    private StatisticItem users;
}
