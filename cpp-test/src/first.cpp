#include "first.h"

#if BUILD == 1
#warning "This is build 1"
#elif BUILD == 2
#warning "This is build 2"
#endif

void bar();

void foo()
{
  bob();
}

int main()
{
  bar();
  foo();
}
