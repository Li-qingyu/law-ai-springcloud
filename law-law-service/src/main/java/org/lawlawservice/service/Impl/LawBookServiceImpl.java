package org.lawlawservice.service.Impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import org.lawcommoncore.annotation.RecordActivity;
import org.lawcommoncore.dto.LawBookPageDTO;
import org.lawcommoncore.entity.LawBook;
import org.lawcommoncore.result.PageResult;
import org.lawlawservice.exception.LawBookException;
import org.lawlawservice.mapper.LawArticleMapper;
import org.lawlawservice.mapper.LawBookMapper;
import org.lawlawservice.service.LawBookService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

import static org.lawcommoncore.constant.ActivitiesConstant.*;

@Service
public class LawBookServiceImpl implements LawBookService {
    @Autowired
    private LawBookMapper lawBookMapper;
    @Autowired
    private LawArticleMapper lawArticleMapper;

    @Override
    public LawBook queryById(Long id) {
        if(id == null){
            throw new LawBookException("id不能为空");
        }
        return lawBookMapper.queryById(id);
    }

    @Override
    public List<LawBook> list() {
        List<LawBook> list =lawBookMapper.list();
        if(list == null){
            throw new LawBookException("没有法律书");
        }
        return list;
    }

    @Override
    public PageResult queryByPage(LawBookPageDTO lawBookPageDTO) {
        if(lawBookPageDTO.getPage() == null || lawBookPageDTO.getPageSize() == null) {
            throw new LawBookException("分页参数不能为空");
        }
        PageHelper.startPage(lawBookPageDTO.getPage(), lawBookPageDTO.getPageSize());
        Page<LawBook> page = lawBookMapper.queryByPage(lawBookPageDTO.getName());
        return new PageResult(page.getTotal(), page.getResult());
    }
    @RecordActivity(type = BOOK_ADD, titleTemplate = "'添加法律书籍：' + #lawBook.name")
    @Override
    public void add(LawBook lawBook) {
        if(lawBook == null || lawBook.getName() == null || lawBook.getName().isEmpty()) {
            throw new LawBookException("法律书名称不能为空");
        }
        lawBookMapper.insert(lawBook);
    }
    @RecordActivity(type = BOOK_UPDATE, titleTemplate = "'更新法律书籍：' + #lawBook.name")
    @Override
    public void update(LawBook lawBook) {
        if(lawBook == null || lawBook.getId() == null) {
            throw new LawBookException("法律书 ID 不能为空");
        }
        if(lawBook.getName() == null || lawBook.getName().isEmpty()) {
            throw new LawBookException("法律书名称不能为空");
        }
        LawBook existingBook = lawBookMapper.queryById(lawBook.getId().longValue());
        if(existingBook == null) {
            throw new LawBookException("法律书不存在");
        }
        BeanUtils.copyProperties(lawBook, existingBook);
        lawBookMapper.update(existingBook);
    }
    @RecordActivity(type = BOOK_DELETE, titleTemplate = "'删除法律书籍：' + #ids")
    @Override
    public void delete(List<Long> ids) {
        if(ids == null) {
            throw new LawBookException("法律书 ID 不能为空");
        }
        //判断是否还有关联的法律条文
        for(Long id : ids) {
            if(lawArticleMapper.queryByBookIdCount(id)> 0) {
                throw new LawBookException("法律书下有关联的法律条文，请先删除关联的法律条文");
            }
        }

        lawBookMapper.delete(ids);
    }


}
