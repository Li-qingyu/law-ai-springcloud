package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CarouselVO {
    private long id;
    private String title;
    private String subTitle;
    private String buttonText;
    private String imageUrl;
}
