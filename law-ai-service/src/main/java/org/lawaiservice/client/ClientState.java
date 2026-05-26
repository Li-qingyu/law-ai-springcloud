package org.lawaiservice.client;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;


@Data
@AllArgsConstructor
@NoArgsConstructor
public class ClientState {
    private String status;
    private Map<String, Object> data;
    private String message;
}
