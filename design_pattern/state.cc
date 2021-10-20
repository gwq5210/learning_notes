#include "state.h"

NormalVoteState VoteManager::normal_vote_state;
RepeatVoteState VoteManager::repeat_vote_state;

void NormalVoteState::vote(VoteManager* manager, const std::string& username) {
  manager->inc_vote(username);
  manager->set_state(&VoteManager::repeat_vote_state);
  printf("%s, 投票成功!\n", username.c_str());
}

int main(int argc, char* argv[]) {
  VoteManager manager;
  manager.vote("gwq5210");
  manager.vote("gwq5210");
  return 0;
}