#include <cstdio>

#include <string>
#include <unordered_map>

class VoteManager;

class VoteState {
 public:
  virtual void vote(VoteManager* manager, const std::string& username) {}
};

class NormalVoteState: public VoteState {
 public:
  virtual void vote(VoteManager* manager, const std::string& username);
};

class RepeatVoteState: public VoteState {
 public:
  virtual void vote(VoteManager* manager, const std::string& username) {
    printf("%s, 请不要重复投票!\n", username.c_str());
  }
};

class VoteManager {
 public:
  static NormalVoteState normal_vote_state;
  static RepeatVoteState repeat_vote_state;

  VoteManager(): state_(&normal_vote_state) {}
  void vote(const std::string& username) {
    state_->vote(this, username);
  }

  void inc_vote(const std::string& username, int count = 1) {
    vote_map_[username] += count;
  }
  int vote_count(const std::string& username) {
    auto it = vote_map_.find(username);
    if (it != vote_map_.end()) {
      return it->second;
    }
    return 0;
  }

  void set_state(VoteState* state) { state_ = state; }
  VoteState* state() { return state_; }
 
 private:
  VoteState* state_;
  std::unordered_map<std::string, int> vote_map_;
};