package org.lawaiservice.config;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.openai.OpenAiChatModel;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import static org.lawcommoncore.context.PromptContext.PROMPT_CONSULT;


@Configuration
public class CommonConfiguration {


    @Bean
    public ChatClient chatClient(OpenAiChatModel openAiChatModel,ChatMemory chatMemory) {
        return  ChatClient
                .builder(openAiChatModel)
                .defaultSystem(PROMPT_CONSULT)
                .defaultAdvisors(
                        new SimpleLoggerAdvisor(),
                        MessageChatMemoryAdvisor
                                .builder(chatMemory)
                                .build()

                )
                .build();
    }


/*    @Bean
    public ChatClient pdfChatClient(OpenAiChatModel openAiChatModel, ChatMemory chatMemory,
            VectorStore vectorStore) {
        return ChatClient
                .builder(openAiChatModel)
                .defaultSystem("请根据上下文回答问题，遇到上下文没有的问题，不要随意编造")
                .defaultAdvisors(
                        SimpleLoggerAdvisor.builder().build(),
                        MessageChatMemoryAdvisor.builder(chatMemory).build(),
                        QuestionAnswerAdvisor
                                .builder(vectorStore)
                                .searchRequest(
                                        SearchRequest.builder() // 向量检索的请求参数
                                                .similarityThreshold(0.5d) // 相似度阈值
                                                .topK(2) // 返回的文档片段数量
                                                .build()
                                ).build()
                )
                .build();
    }*/


}
