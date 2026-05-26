package org.lawaiservice.utils;

import com.alibaba.fastjson.JSONObject;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.function.Consumer;

public class HttpClient {
    private static final int TIMEOUT_MSEC =120000 ;

    //构建post请求
    public static String doPostJson(String url, Object requestBody) throws IOException {
        CloseableHttpClient httpClient = HttpClients.createDefault();
        CloseableHttpResponse response = null;
        String resultString = "";

        try {
            HttpPost httpPost = new HttpPost(url);

            if (requestBody != null) {
                String jsonBody = JSONObject.toJSONString(requestBody);
                StringEntity entity = new StringEntity(jsonBody, "utf-8");
                entity.setContentEncoding("utf-8");
                entity.setContentType("application/json");
                httpPost.setEntity(entity);
            }

            httpPost.setConfig(builderRequestConfig());

            response = httpClient.execute(httpPost);

            resultString = EntityUtils.toString(response.getEntity(), "UTF-8");
        } catch (Exception e) {
            throw e;
        } finally {
            try {
                response.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        return resultString;
    }

    /**
     * 流式 POST 请求，返回 SSE 事件的 Flux
     */
    public static Flux<String> doPostJsonStreaming(String url, Object requestBody) {
        WebClient webClient = WebClient.builder()
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(1024 * 1024))
                .build();

        String jsonBody = JSONObject.toJSONString(requestBody);

        return webClient.post()
                .uri(url)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(jsonBody)
                .retrieve()
                .bodyToFlux(String.class);
    }

    /**
     * 流式 POST 请求，使用回调方式逐行处理 SSE 事件
     */
    public static void doPostJsonStreaming(String url, Object requestBody, Consumer<String> onEvent, Runnable onComplete) throws IOException {
        CloseableHttpClient httpClient = HttpClients.createDefault();
        CloseableHttpResponse response = null;

        try {
            HttpPost httpPost = new HttpPost(url);

            if (requestBody != null) {
                String jsonBody = JSONObject.toJSONString(requestBody);
                StringEntity entity = new StringEntity(jsonBody, "utf-8");
                entity.setContentEncoding("utf-8");
                entity.setContentType("application/json");
                httpPost.setEntity(entity);
            }

            httpPost.setConfig(builderRequestConfig());

            response = httpClient.execute(httpPost);

            try (InputStream inputStream = response.getEntity().getContent();
                 BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {

                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.startsWith("data: ")) {
                        String data = line.substring(6).trim();
                        if (!data.isEmpty()) {
                            onEvent.accept(data);
                        }
                    }
                }
            }

            onComplete.run();
        } catch (Exception e) {
            throw e;
        } finally {
            try {
                if (response != null) {
                    response.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private static RequestConfig builderRequestConfig() {
        return RequestConfig.custom()
                .setConnectTimeout(TIMEOUT_MSEC)
                .setConnectionRequestTimeout(TIMEOUT_MSEC)
                .setSocketTimeout(TIMEOUT_MSEC).build();
    }

}
