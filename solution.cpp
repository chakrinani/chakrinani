#include <vector>
#include <unordered_map>
using namespace std;

class Solution {
public:
    vector<int> numOfSubarrays(vector<int>& nums, vector<vector<int>>& queries) {
        vector<int> result;
        
        for (auto& query : queries) {
            int left = query[0];
            int right = query[1];
            int threshold = query[2];
            
            // Count frequency of each element in the subarray [left, right]
            unordered_map<int, int> freq;
            for (int i = left; i <= right; i++) {
                freq[nums[i]]++;
            }
            
            // Find the best element that appears >= threshold times
            // Priority: highest frequency, then smallest value
            int answer = -1;
            int maxFreq = 0;
            
            for (auto& pair : freq) {
                if (pair.second >= threshold) {
                    if (answer == -1 || pair.second > maxFreq || 
                        (pair.second == maxFreq && pair.first < answer)) {
                        answer = pair.first;
                        maxFreq = pair.second;
                    }
                }
            }
            
            result.push_back(answer);
        }
        
        return result;
    }
};

// Alternative solution with better time complexity for large inputs
class SolutionOptimized {
public:
    vector<int> numOfSubarrays(vector<int>& nums, vector<vector<int>>& queries) {
        vector<int> result;
        
        for (auto& query : queries) {
            int left = query[0];
            int right = query[1];
            int threshold = query[2];
            
            unordered_map<int, int> freq;
            for (int i = left; i <= right; i++) {
                freq[nums[i]]++;
            }
            
            int answer = -1;
            int maxFreq = 0;
            
            for (auto& [val, count] : freq) {
                if (count >= threshold) {
                    if (answer == -1 || count > maxFreq || 
                        (count == maxFreq && val < answer)) {
                        answer = val;
                        maxFreq = count;
                    }
                }
            }
            
            result.push_back(answer);
        }
        
        return result;
    }
};