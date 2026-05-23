package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class StatisticItem implements Serializable {
    private Integer count;
    private Double trend;
}
