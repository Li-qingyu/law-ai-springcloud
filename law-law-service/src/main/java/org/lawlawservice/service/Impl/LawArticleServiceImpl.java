package org.lawlawservice.service.Impl;


import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.lawcommoncore.annotation.RecordActivity;
import org.lawcommoncore.dto.LawArticlesDTO;
import org.lawcommoncore.dto.LawArticlesPageDTO;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.event.LawArticleSyncEvent;
import org.lawcommoncore.result.PageResult;
import org.lawlawservice.exception.LawArticlesException;
import org.lawlawservice.feign.MilvusFeignClient;
import org.lawlawservice.mapper.LawArticleMapper;
import org.lawlawservice.service.LawArticleService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static org.lawcommoncore.constant.ActivitiesConstant.*;


@Service
@Slf4j
public class LawArticleServiceImpl implements LawArticleService {
    @Autowired
    private LawArticleMapper lawArticleMapper;
    @Autowired
    private MilvusFeignClient milvusFeignClient;
    @Autowired
    private ApplicationEventPublisher eventPublisher;
    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 添加法律条文
     * @param lawArticlesDTO
     */
    @Override
    @RecordActivity(type = LAW_ADD, titleTemplate = "'添加法律条文：' + #lawArticlesDTO.articleTitle")
    @Transactional(rollbackFor = Exception.class)
    public void add(LawArticlesDTO lawArticlesDTO) {
        LawArticle lawArticle = new LawArticle();
        BeanUtils.copyProperties(lawArticlesDTO, lawArticle);
        lawArticle.setArticleOrder(parseArticleOrder(lawArticlesDTO.getArticleTitle()));
        lawArticle.setCreateTime(LocalDateTime.now());
        lawArticle.setUpdateTime(LocalDateTime.now());
        lawArticleMapper.insert(lawArticle);

        eventPublisher.publishEvent(new LawArticleSyncEvent( this, lawArticle, LawArticleSyncEvent.SyncType.ADD));
        log.info("添加法律条文成功{}",lawArticle);
    }

    @Override
    public PageResult list(LawArticlesPageDTO lawArticlesPageDTO) {
        PageHelper.startPage(lawArticlesPageDTO.getPage(),lawArticlesPageDTO.getPageSize());
        List<LawArticle>  list = lawArticleMapper.list(lawArticlesPageDTO);
        Page<LawArticle> p=(Page<LawArticle>)  list;//Page对象是PageHelper的子类,里面封装好了查询的结果
        return new PageResult(p.getTotal(),p.getResult());
    }

    @Override
    public LawArticle get(Long id) {
        log.info("查询法律条文:{}", id);
        if(id==null){
            throw new LawArticlesException("id不能为空");
        }
        return lawArticleMapper.get(id);
    }
    @RecordActivity(type = LAW_UPDATE, titleTemplate = "'更新法律条文：' + #lawArticlesDTO.articleTitle")
    @Transactional(rollbackFor = Exception.class)
    @Override
    public void update(LawArticlesDTO lawArticlesDTO) {
        if(lawArticlesDTO.getId()==null){
            throw new LawArticlesException("id 不能为空");
        }
        LawArticle originalArticle = lawArticleMapper.get(lawArticlesDTO.getId());
        if (originalArticle == null) {
            throw new LawArticlesException("法律条文不存在");
        }
        LawArticle lawArticle = new LawArticle();
        BeanUtils.copyProperties(lawArticlesDTO, lawArticle);
        lawArticle.setUpdateTime(LocalDateTime.now());
        boolean titleOrContentChanged =
                (!lawArticlesDTO.getArticleTitle().equals(originalArticle.getArticleTitle())) ||
                        (lawArticlesDTO.getContent() != null && !lawArticlesDTO.getContent().equals(originalArticle.getContent()));
        if (titleOrContentChanged) {
            lawArticle.setArticleOrder(parseArticleOrder(lawArticlesDTO.getArticleTitle()));
        } else {
            lawArticle.setArticleOrder(originalArticle.getArticleOrder());
        }
        lawArticleMapper.update(lawArticle);
        eventPublisher.publishEvent(new LawArticleSyncEvent( this, lawArticle, LawArticleSyncEvent.SyncType.UPDATE));

        log.info("修改法律条文成功{}",lawArticle);
    }
    @RecordActivity(type = LAW_DELETE, titleTemplate = "'删除法律条文：ID=' + #ids")
    @Transactional(rollbackFor = Exception.class)
    @Override
    public void delete(List<Long> ids) {
        if(ids==null||ids.isEmpty()){
            throw new LawArticlesException("id不能为空");
        }
        lawArticleMapper.delete(ids);

        eventPublisher.publishEvent(new LawArticleSyncEvent( this, ids, LawArticleSyncEvent.SyncType.DELETE));
        log.info("删除法律条文成功{}",ids);
    }

    @RecordActivity(type = LAW_IMPORT, titleTemplate = "'导入法律条文从Excel：' + #file.originalFilename")
    @Transactional(rollbackFor = Exception.class)
    @Override
    public String importExcel(MultipartFile file,Integer bookId) {
        log.info("开始导入 Excel 文件:{}", file.getOriginalFilename());

        List<LawArticle> articles = new ArrayList<>();
        int successCount = 0;
        int failCount = 0;


        try (Workbook workbook = new XSSFWorkbook(file.getInputStream())) {
            Sheet sheet = workbook.getSheetAt(0);

            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");

            for (int i = 1; i <= sheet.getLastRowNum(); i++) {
                Row row = sheet.getRow(i);
                if (row == null) continue;

                LawArticle article = new LawArticle();

                Cell articleTitleCell = row.getCell(1);
                String articleTitle = articleTitleCell != null ? articleTitleCell.getStringCellValue() : "";
                if (articleTitle.trim().isEmpty()) {
                    log.warn("跳过第 {} 行：条文标题为空", i + 1);
                    failCount++;
                    continue;
                }
                article.setArticleTitle(articleTitle);

                Cell contentCell = row.getCell(2);
                String content = contentCell != null ? contentCell.getStringCellValue() : "";
                if (content.trim().isEmpty()) {
                    log.warn("跳过第 {} 行 [{}]：条文内容为空", i + 1, articleTitle);
                    failCount++;
                    continue;
                }
                article.setContent(content);

                Date publishDate = parseDateFromCell(row.getCell(3), "发布日期", i + 1, articleTitle);
                if (publishDate == null) {
                    log.warn("跳过第 {} 行 [{}]：发布日期为空或格式错误", i + 1, articleTitle);
                    failCount++;
                    continue;
                }
                article.setPublishDate(publishDate);

                Date effectiveDate = parseDateFromCell(row.getCell(4), "生效日期", i + 1, articleTitle);
                if (effectiveDate == null) {
                    log.warn("跳过第 {} 行 [{}]：生效日期为空或格式错误", i + 1, articleTitle);
                    failCount++;
                    continue;
                }
                article.setEffectiveDate(effectiveDate);

                article.setCreateTime(LocalDateTime.now());
                article.setUpdateTime(LocalDateTime.now());

                articles.add(article);
            }

            if (!articles.isEmpty()) {
                for (LawArticle article : articles) {
                    try {
                        article.setArticleOrder(parseArticleOrder(article.getArticleTitle()));
                        article.setLawBookId(bookId);
                        lawArticleMapper.insert(article);
                        successCount++;
                    } catch (Exception e) {
                        failCount++;
                        // 2. 将日志级别调整为 warn，并明确提示是“跳过”
                        log.warn("跳过重复或错误的法律条文 [{}]: {}", article.getArticleTitle(), e.getMessage());
                    }
                }
                // 3. 优化日志输出，增加总计信息
                log.info("导入完成。总计: {}, 成功: {}, 跳过/失败: {}", articles.size(), successCount, failCount);
            }
            return "导入完成。总计: "+ articles.size() +",成功:"+ successCount + ", 跳过/失败: " + failCount;
        } catch (IOException e) {
            log.error("导入 Excel 文件失败", e);
            throw new RuntimeException("导入 Excel 文件失败：" + e.getMessage());
        }

    }
    /**
     * 从 Excel 单元格解析日期
     * @param cell 单元格
     * @param fieldName 字段名称（用于日志）
     * @param rowNum 行号（用于日志）
     * @param articleTitle 条文标题（用于日志）
     * @return 解析后的日期，如果解析失败返回 null
     */
    private Date parseDateFromCell(Cell cell, String fieldName, int rowNum, String articleTitle) {
        if (cell == null) {
            return null;
        }

        try {
            if (cell.getCellType() == CellType.NUMERIC && DateUtil.isCellDateFormatted(cell)) {
                // 情况 1: 数值类型的日期格式（Excel 标准日期格式）
                return DateUtil.getJavaDate(cell.getNumericCellValue());
            } else if (cell.getCellType() == CellType.STRING) {
                // 情况 2: 字符串类型的日期，使用正则表达式判断
                String dateString = cell.getStringCellValue().trim();
                if (!dateString.isEmpty() && dateString.matches("\\d{4}-\\d{1,2}-\\d{1,2}")) {
                    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
                    return sdf.parse(dateString);
                }
            }
        } catch (Exception e) {
            log.error("{}解析失败 [第{}行 - {}]：{}", fieldName, rowNum, articleTitle, cell.toString(), e);
        }

        return null;
    }
    @Override
    public Integer count() {
        return lawArticleMapper.count();
    }

    @Override
    public Integer countOneWeekAgo() {
        return lawArticleMapper.countOneWeekAgo();
    }

    @Override
    public String addLawArticlesToMilvusAsync(Integer lawBookId) {
        // 1. 生成唯一任务ID
        String taskId = UUID.randomUUID().toString();

        // 2. 在 Redis 中初始化任务状态 (设置过期时间，防止垃圾数据堆积)
        stringRedisTemplate.opsForValue().set("milvus_task:" + taskId, "PROCESSING", 10, TimeUnit.MINUTES);

        // 3. 触发异步任务，将 taskId 传进去
        executeMilvusSyncAsync(lawBookId, taskId);

        // 4. 立即返回 taskId 给前端
        return taskId;
    }
    @Async
    public void executeMilvusSyncAsync(Integer lawBookId, String taskId) {
        try {
            log.info("开始异步同步任务: {}", taskId);
            List<LawArticle> articles = lawArticleMapper.queryByBook(lawBookId);

            if (articles == null || articles.isEmpty()) {
                stringRedisTemplate.opsForValue().set("milvus_task:" + taskId, "SUCCESS: 没有数据需要同步", 10, TimeUnit.MINUTES);
                return;
            }

            // 调用 Milvus 同步逻辑
            milvusFeignClient.addLawArticles(articles);

            // 5. 更新 Redis 状态为成功
            stringRedisTemplate.opsForValue().set("milvus_task:" + taskId, "SUCCESS: 同步完成", 10, TimeUnit.MINUTES);
            log.info("异步同步任务完成: {}", taskId);
        } catch (Exception e) {
            log.error("异步同步任务失败: {}", taskId, e);
            // 6. 更新 Redis 状态为失败
            stringRedisTemplate.opsForValue().set("milvus_task:" + taskId, "FAILED: " + e.getMessage(), 10, TimeUnit.MINUTES);
        }
    }





    /**
     * 从法律条文标题中提取条文序号
     * 支持格式：第一条、第二十五条、第一百二十五条、第一千零四十九条等
     * @param articleTitle 条文标题
     * @return 条文序号，如果无法解析返回 null
     */
    private Integer parseArticleOrder(String articleTitle) {
        if (articleTitle == null || articleTitle.trim().isEmpty()) {//trim用于去除字符串前后的空格
            return null;
        }

        // 匹配"第 X 条"格式
        Pattern pattern = Pattern.compile("第\\s*([零一二三四五六七八九十百千0-9]+)\\s*条");
        Matcher matcher = pattern.matcher(articleTitle);
        boolean found = matcher.find();
        log.info("匹配结果：{}", found);
        if (!found) {
            return null;
        }

        String numberStr = matcher.group(1);

        // 如果是阿拉伯数字，直接转换
        if (numberStr.matches("\\d+")) {
            int result = Integer.parseInt(numberStr);
            return result <= 1500 ? result : null;
        }

        // 中文数字转换（1-1500）
        return chineseNumberToArabic(numberStr);
    }

    /**
     * 将中文数字转换为阿拉伯数字（支持 1-1500）
     * 支持：零、一、二、三...十、百、千
     * @param chinese 中文数字字符串
     * @return 阿拉伯数字
     */
    private Integer chineseNumberToArabic(String chinese) {
        if (chinese == null || chinese.isEmpty()) {
            return null;
        }

        // 中文数字映射
        Map<Character, Integer> charMap = new HashMap<>();
        charMap.put('零', 0);
        charMap.put('一', 1);
        charMap.put('二', 2);
        charMap.put('三', 3);
        charMap.put('四', 4);
        charMap.put('五', 5);
        charMap.put('六', 6);
        charMap.put('七', 7);
        charMap.put('八', 8);
        charMap.put('九', 9);
        charMap.put('十', 10);
        charMap.put('百', 100);
        charMap.put('千', 1000);

        // 阿拉伯数字映射
        Map<Character, Integer> digitMap = new HashMap<>();
        digitMap.put('0', 0);
        digitMap.put('1', 1);
        digitMap.put('2', 2);
        digitMap.put('3', 3);
        digitMap.put('4', 4);
        digitMap.put('5', 5);
        digitMap.put('6', 6);
        digitMap.put('7', 7);
        digitMap.put('8', 8);
        digitMap.put('9', 9);

        int result = 0;

        // 处理"一千 XXX"格式（1000-1500）
        if (chinese.contains("千")) {
            String[] parts = chinese.split("千");
            int thousandPart = 0;

            // 处理千位
            if (parts.length > 0 && !parts[0].isEmpty()) {
                if (parts[0].matches("\\d")) {
                    thousandPart = digitMap.get(parts[0].charAt(0));
                } else {
                    thousandPart = charMap.getOrDefault(parts[0].charAt(0), 1);
                }
            } else {
                thousandPart = 1;
            }

            result += thousandPart * 1000;

            // 处理千位之后的部分
            if (parts.length > 1 && !parts[1].isEmpty()) {
                Integer remainder = parseRemainder(parts[1], charMap, digitMap);
                if (remainder != null) {
                    result += remainder;
                }
            }
        }
        // 处理"九百 XX"格式（900-999）
        else if (chinese.contains("百")) {
            String[] parts = chinese.split("百");
            int hundredPart = 0;

            // 处理百位
            if (parts.length > 0 && !parts[0].isEmpty()) {
                if (parts[0].matches("\\d")) {
                    hundredPart = digitMap.get(parts[0].charAt(0));
                } else {
                    hundredPart = charMap.getOrDefault(parts[0].charAt(0), 0);
                }
            }

            result += hundredPart * 100;

            // 处理百位之后的部分
            if (parts.length > 1 && !parts[1].isEmpty()) {
                Integer remainder = parseRemainder(parts[1], charMap, digitMap);
                if (remainder != null) {
                    result += remainder;
                }
            }
        }
        // 处理"九十 XX"格式（90-999）
        else if (chinese.contains("十")) {
            String[] parts = chinese.split("十");

            // 处理十位
            if (parts.length > 0) {
                if (parts[0].isEmpty()) {
                    result += 10;
                } else {
                    int tenPart;
                    if (parts[0].matches("\\d")) {
                        tenPart = digitMap.get(parts[0].charAt(0));
                    } else {
                        tenPart = charMap.getOrDefault(parts[0].charAt(0), 0);
                    }
                    result += tenPart * 10;
                }
            }

            // 处理十位之后的个位
            if (parts.length > 1 && !parts[1].isEmpty()) {
                int unitPart;
                if (parts[1].matches("\\d")) {
                    unitPart = digitMap.get(parts[1].charAt(0));
                } else {
                    unitPart = charMap.getOrDefault(parts[1].charAt(0), 0);
                }
                result += unitPart;
            }
        }
        // 处理简单情况（1-9）
        else {
            if (chinese.matches("\\d")) {
                result = digitMap.get(chinese.charAt(0));
            } else if (chinese.length() == 1) {
                result = charMap.getOrDefault(chinese.charAt(0), 0);
            }
        }

        // 验证范围
        return (result >= 1 && result <= 1500) ? result : null;
    }

    /**
     * 解析百位或千位之后的剩余部分
     * @param remainder 剩余部分
     * @param charMap 中文字符映射
     * @param digitMap 阿拉伯数字映射
     * @return 解析后的数字
     */
    private Integer parseRemainder(String remainder, Map<Character, Integer> charMap,
                                   Map<Character, Integer> digitMap) {
        if (remainder == null || remainder.isEmpty()) {
            return 0;
        }

        int result = 0;

        // 处理"零 XX"格式
        if (remainder.startsWith("零")) {
            remainder = remainder.substring(1);
            if (remainder.isEmpty()) {
                return 0;
            }
        }

        // 处理"几十"格式
        if (remainder.contains("十")) {
            String[] parts = remainder.split("十");

            if (parts.length > 0 && !parts[0].isEmpty()) {
                int tenPart;
                if (parts[0].matches("\\d")) {
                    tenPart = digitMap.get(parts[0].charAt(0));
                } else {
                    tenPart = charMap.getOrDefault(parts[0].charAt(0), 0);
                }
                result += tenPart * 10;
            } else if (parts.length > 0 && parts[0].isEmpty()) {
                result += 10;
            }

            if (parts.length > 1 && !parts[1].isEmpty()) {
                int unitPart;
                if (parts[1].matches("\\d")) {
                    unitPart = digitMap.get(parts[1].charAt(0));
                } else {
                    unitPart = charMap.getOrDefault(parts[1].charAt(0), 0);
                }
                result += unitPart;
            }
        }
        // 处理个位
        else if (remainder.length() == 1) {
            if (remainder.matches("\\d")) {
                result = digitMap.get(remainder.charAt(0));
            } else {
                result = charMap.getOrDefault(remainder.charAt(0), 0);
            }
        }

        return result;
    }




}



