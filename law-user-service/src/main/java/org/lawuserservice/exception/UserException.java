package org.lawuserservice.exception;

import org.lawcommoncore.exception.BaseException;

public class UserException extends BaseException {
  public UserException(){
      super();
  }

  public UserException(String message) {
        super(message);
    }
}
