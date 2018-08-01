#include <unistd.h>
#include <iostream>
#include <sys/types.h>
#include <unistd.h>    

int main(int argc, char **argv) {
  std::cout << getpid() << std::endl;
  for (int i = 0;; i++) {
    std::cout << "Having fun " << i << std::endl;
    sleep (1);
  }
}
