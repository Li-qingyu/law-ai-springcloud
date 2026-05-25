package org.lawaiservice.config;

import io.milvus.client.MilvusServiceClient;
import io.milvus.param.ConnectParam;
import io.milvus.v2.client.ConnectConfig;
import io.milvus.v2.client.MilvusClientV2;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;

@Configuration
public class MilvusVectorConfiguration {

    @Value("${spring.ai.vectorstore.milvus.databaseName}")
    private String databaseName;
    @Value("${spring.ai.vectorstore.milvus.url}")
    private String url;

    /**
     * 创建 Milvus 客户端并指定数据库
     */
    @Bean
    public MilvusClientV2 milvusClientV2() {

        ConnectConfig connectConfig = ConnectConfig.builder()
                .uri(url)
                .dbName(databaseName)           // 默认数据库，之后操作可省略 .databaseName()
                .build();
        return new MilvusClientV2(connectConfig);
    }




}
