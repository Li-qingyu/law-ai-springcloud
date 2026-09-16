package org.lawlawservice.service.Impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.annotation.RecordActivity;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.dto.LawCaseDTO;
import org.lawcommoncore.dto.LawCasePageDTO;
import org.lawcommoncore.dto.LawCaseStatusDTO;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.event.LawCaseSyncEvent;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.vo.LawCaseVO;
import org.lawcommonsecurity.annotation.RequireRole;
import org.lawcommonsecurity.constant.UserRole;
import org.lawlawservice.exception.LawCaseException;
import org.lawlawservice.feign.MilvusFeignClient;
import org.lawlawservice.mapper.LawCaseCollectionMapper;
import org.lawlawservice.mapper.LawCaseMapper;
import org.lawlawservice.service.LawCaseService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import static org.lawcommoncore.constant.ActivitiesConstant.*;

@Slf4j
@Service
public class LawCaseServiceImpl implements LawCaseService {
    @Autowired
    private LawCaseMapper lawCaseMapper;

    @Autowired
    private LawCaseCollectionMapper lawCaseCollectionMapper;

    @Autowired
    private ApplicationEventPublisher eventPublisher;
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    @Autowired
    private MilvusFeignClient milvusFeignClient;

    @Transactional(rollbackFor = Exception.class)
    @RecordActivity(type = CASE_ADD, titleTemplate = "'添加案例：' + #lawCaseDTO.title")
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    @Override
    public void save(LawCaseDTO lawCaseDTO) {
        LawCase lawCase = new LawCase();
        BeanUtils.copyProperties(lawCaseDTO, lawCase);
        //发布时间设置为创建时间
        lawCase.setStatus(1);
        lawCase.setUpdateTime(LocalDateTime.now());
        lawCase.setCreateTime(LocalDateTime.now());
        lawCase.setPublishTime(LocalDateTime.now());
        lawCaseMapper.insert(lawCase);

        eventPublisher.publishEvent(new LawCaseSyncEvent(this, lawCase, LawCaseSyncEvent.SyncType.ADD));

    }

    @Override
    public PageResult queryByPage(LawCasePageDTO lawCasePageDTO) {
        PageHelper.startPage(lawCasePageDTO.getPage(), lawCasePageDTO.getPageSize());
        Page<LawCaseVO> page = lawCaseMapper.queryByPage(lawCasePageDTO);
        return new PageResult(page.getTotal(), page.getResult());
    }

    @Override
    public LawCase get(Long id) {
        if(id == null){
            throw new LawCaseException("id不能为空");
        }
        return lawCaseMapper.get(id);

    }
    @RecordActivity(type = CASE_UPDATE, titleTemplate = "'更新案例：' + #lawCaseDTO.title")
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    @Transactional(rollbackFor = Exception.class)
    @Override
    public void update(LawCaseDTO lawCaseDTO) {
        LawCase lawCase = new LawCase();
        BeanUtils.copyProperties(lawCaseDTO, lawCase);
        lawCase.setUpdateTime(LocalDateTime.now());
        lawCaseMapper.update(lawCase);

        eventPublisher.publishEvent(new LawCaseSyncEvent(this, lawCase, LawCaseSyncEvent.SyncType.UPDATE));

    }
    @RecordActivity(type = CASE_DELETE, titleTemplate = "'删除案例：' + #id")
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    @Transactional(rollbackFor = Exception.class)
    @Override
    public void delete(Long id) {
        if(id == null){
            throw new LawCaseException("id不能为空");
        }
        //查询是否上架
        LawCase lawCase = lawCaseMapper.get(id);
        if(lawCase.getStatus() == 1){
            throw new LawCaseException("请先下架");
        }
        //删除相关的案例收藏
        lawCaseCollectionMapper.cancelCollection(lawCase.getId().intValue(), BaseContext.getCurrentId());

        lawCaseMapper.delete(id);

        eventPublisher.publishEvent(new LawCaseSyncEvent(this, List.of(id), LawCaseSyncEvent.SyncType.DELETE));
    }

    @Override
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public void batchToggleStatus(LawCaseStatusDTO lawCaseStatusDTO) {
        if(lawCaseStatusDTO.getIds() == null){
            throw new LawCaseException("ids不能为空");
        }
        if(lawCaseStatusDTO.getStatus() == null){
            throw new LawCaseException("status不能为空");
        }
        lawCaseMapper.batchToggleStatus(lawCaseStatusDTO);
    }

    @Override
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public Integer count() {
        return lawCaseMapper.count();
    }

    @Override
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public Integer countOneWeekAgo() {
        return lawCaseMapper.countOneWeekAgo();
    }

    @Override
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public String addLawCaseToMilvusAsync() {
        //1。生成任务ID
        String taskId= UUID.randomUUID().toString();
        //2.在Redis中初始化任务状态(设置过期时间，防止垃圾数据堆积)
        stringRedisTemplate.opsForValue().set("milvus_task:" + taskId, "PROCESSING", 10, TimeUnit.MINUTES);
        executeAddLawCaseToMilvusTask(taskId);
        return taskId;
    }
    @Async
    public void executeAddLawCaseToMilvusTask(String taskId) {
        try {
            log.info("开始异步同步任务: {}", taskId);
            //1.获取任务状态
            String taskStatus = stringRedisTemplate.opsForValue().get("milvus_task:" + taskId);
            List<LawCase> lawCases= lawCaseMapper.all();
            if (lawCases.isEmpty()) {
                //3.更新任务状态
                stringRedisTemplate.opsForValue().set("milvus_task:" + taskId, "SUCCESS: 没有数据需要同步", 10, TimeUnit.MINUTES);
                return;
            }
            if ("PROCESSING".equals(taskStatus)) {
                //2.执行任务
                milvusFeignClient.addLawCases(lawCases);
                //3.更新任务状态
                stringRedisTemplate.opsForValue().set("milvus_task:"+taskId, "SUCCESS: 同步完成", 10, TimeUnit.MINUTES);
            }
        }catch (Exception e){
            log.error("异步同步任务失败: {}", taskId, e);
            stringRedisTemplate.opsForValue().set("milvus_task:" + taskId, "FAILED: " + e.getMessage(), 10, TimeUnit.MINUTES);
        }

    }

    @Override
    public LawCaseVO getCard(Long id) {
        return lawCaseMapper.getCard(id);
    }

}
