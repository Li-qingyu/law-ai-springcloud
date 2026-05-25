package org.lawlawservice.service;


import org.lawcommoncore.dto.SearchDTO;
import org.lawcommoncore.result.PageResult;

public interface SearchService {
    PageResult search(SearchDTO searchDTO);
}
