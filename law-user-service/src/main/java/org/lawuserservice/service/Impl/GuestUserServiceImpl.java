package org.lawuserservice.service.Impl;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.entity.GuestUser;
import org.lawuserservice.mapper.GuestUserMapper;
import org.lawuserservice.service.GuestUserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@Slf4j
public class GuestUserServiceImpl implements GuestUserService {

    @Autowired
    private GuestUserMapper guestUserMapper;

    @Override
    public GuestUser init(String guestKey, String ipAddress, String userAgent) {
        GuestUser existing = guestUserMapper.getByGuestKey(guestKey);
        if (existing != null) {
            log.info("游客已存在: guestKey={}", guestKey);
            return existing;
        }

        GuestUser guest = GuestUser.builder()
                .guestKey(guestKey)
                .nickname("游客")
                .questionCount(0)
                .maxQuestion(10)
                .ipAddress(ipAddress)
                .userAgent(userAgent)
                .isDeleted(0)
                .createTime(LocalDateTime.now())
                .updateTime(LocalDateTime.now())
                .build();
        guestUserMapper.insert(guest);
        log.info("新游客创建成功: guestKey={}, id={}", guestKey, guest.getId());
        return guest;
    }

    @Override
    public GuestUser getByGuestKey(String guestKey) {
        return guestUserMapper.getByGuestKey(guestKey);
    }

    @Override
    public boolean canAsk(Integer guestId) {
        if (guestId == null) return false;
        GuestUser guest = guestUserMapper.getById(guestId);
        return guest != null && guest.getQuestionCount() < guest.getMaxQuestion();
    }

    @Override
    public void incrementQuestionCount(Integer guestId) {
        if (guestId == null) return;
        guestUserMapper.incrementQuestionCount(guestId);
    }

    @Override
    public void deleteByGuestId(Integer guestId) {
        if (guestId == null) return;
        GuestUser guest = GuestUser.builder()
                .id(guestId)
                .isDeleted(1)
                .deleteTime(LocalDateTime.now())
                .build();
        guestUserMapper.updateById(guest);
        log.info("游客逻辑删除: id={}", guestId);
    }
}
