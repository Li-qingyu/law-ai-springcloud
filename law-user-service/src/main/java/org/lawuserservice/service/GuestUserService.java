package org.lawuserservice.service;

import org.lawcommoncore.entity.GuestUser;

public interface GuestUserService {

    GuestUser init(String guestKey, String ipAddress, String userAgent);

    GuestUser getByGuestKey(String guestKey);

    boolean canAsk(Integer guestId);

    void incrementQuestionCount(Integer guestId);

    void deleteByGuestId(Integer guestId);
}
