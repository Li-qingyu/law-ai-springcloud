from typing import List


class Solution:
    def merge(self, nums1: List[int], m: int, nums2: List[int], n: int) -> None:
        """
        Do not return anything, modify nums1 in-place instead.
        """
        num1=nums1[:m]

        i=0
        j=0
        for k in range (m+n) :
            if i<m and j<n:
                if num1[i]<nums2[j] :
                    nums1[k]=num1[i]
                    i+=1
                else :
                    nums1[k]=nums2[j]
                    j+=1
            else :
                if j<n:
                    nums1[k]=nums2[j]
                    j+=1
                else :
                    nums1[k]=nums1[i]
                    i+=1

if __name__ == '__main__':
    sol = Solution()
    nums1=[1,2,3,0,0,0]
    m = 3
    n = 3
    nums2=[2,5,6]
    sol.merge(nums1,m,nums2,n)
    print(nums1)
    print(nums2)

